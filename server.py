import os
import io
import time
import asyncio
from typing import AsyncGenerator

from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from mss import mss
from PIL import Image

# ---------- CONFIG ----------
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 9000))  # Render provides $PORT
AUTH_TOKEN = os.environ.get("RA_TOKEN", "mysecret123")
FPS = int(os.environ.get("RA_FPS", 5))
SCALE = float(os.environ.get("RA_SCALE", 1.0))
QUALITY = int(os.environ.get("RA_QUALITY", 70))
# ----------------------------

app = FastAPI()

# Allow requests from any origin (for web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _check_token(token: str | None):
    if (token or "") != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/video")
async def video(request: Request, token: str | None = None):
    _check_token(token)
    boundary = "frame"
    frametime = 1.0 / max(FPS, 1)
    last_time = 0.0

    async def frame_generator() -> AsyncGenerator[bytes, None]:
        nonlocal last_time
        with mss() as sct:
            monitor = sct.monitors[0]  # full virtual screen
            while True:
                if await request.is_disconnected():
                    break

                now = time.time()
                if now - last_time < frametime:
                    await asyncio.sleep(0.001)
                    continue
                last_time = now

                sct_img = sct.grab(monitor)
                pil_img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
                if SCALE != 1.0:
                    w = int(pil_img.width * SCALE)
                    h = int(pil_img.height * SCALE)
                    pil_img = pil_img.resize((max(1, w), max(1, h)), Image.BILINEAR)

                buff = io.BytesIO()
                pil_img.save(buff, format="JPEG", quality=QUALITY, optimize=True)
                data = buff.getvalue()

                yield (
                    b"--" + boundary.encode() + b"\r\n"
                    + b"Content-Type: image/jpeg\r\n"
                    + f"Content-Length: {len(data)}\r\n\r\n".encode()
                    + data + b"\r\n"
                )

    return StreamingResponse(
        frame_generator(),
        media_type=f"multipart/x-mixed-replace; boundary={boundary}"
    )

@app.post("/input")
async def input_event(event: dict = Body(...), token: str | None = None):
    _check_token(token)
    # NOTE: pyautogui won't work on Render for mouse/keyboard events.
    # You could handle events differently or leave it non-functional on headless.
    return {"status": "ok", "note": "input events ignored on Render"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=HOST, port=PORT)
