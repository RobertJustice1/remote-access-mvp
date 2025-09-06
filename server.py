import asyncio
import io
import os
import time
from typing import AsyncGenerator

from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

import pyautogui
from PIL import Image

pyautogui.FAILSAFE = False

# ---------- CONFIG ----------
HOST = os.environ.get("RA_HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 9000))  # Use Render's PORT environment variable
AUTH_TOKEN = os.environ.get("RA_TOKEN", "mysecret123")
FPS = int(os.environ.get("RA_FPS", "10"))
SCALE = float(os.environ.get("RA_SCALE", "1.0"))  # scale 1.0 to match full screen
QUALITY = int(os.environ.get("RA_QUALITY", "70"))
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
        while True:
            if await request.is_disconnected():
                break

            now = time.time()
            if now - last_time < frametime:
                await asyncio.sleep(0.001)
                continue
            last_time = now

            # Capture full screen
            pil = pyautogui.screenshot()
            if SCALE != 1.0:
                w = int(pil.width * SCALE)
                h = int(pil.height * SCALE)
                pil = pil.resize((max(1, w), max(1, h)), Image.BILINEAR)

            buff = io.BytesIO()
            pil.save(buff, format="JPEG", quality=QUALITY, optimize=True)
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
    try:
        mtype = event.get("type")
        if mtype == "mouse_move":
            pyautogui.moveTo(event["x"], event["y"])
        elif mtype == "mouse_click":
            pyautogui.click(button=event.get("button", "left"), clicks=int(event.get("clicks", 1)))
        elif mtype == "mouse_down":
            pyautogui.mouseDown(button=event.get("button", "left"))
        elif mtype == "mouse_up":
            pyautogui.mouseUp(button=event.get("button", "left"))
        elif mtype == "scroll":
            pyautogui.scroll(int(event.get("dy", 0)))
            pyautogui.hscroll(int(event.get("dx", 0)))
        elif mtype == "key_down":
            pyautogui.keyDown(event["key"])
        elif mtype == "key_up":
            pyautogui.keyUp(event["key"])
        elif mtype == "type_text":
            pyautogui.typewrite(event.get("text", ""), interval=0.01)
        elif mtype == "hotkey":
            keys = event.get("keys", [])
            if isinstance(keys, list) and keys:
                pyautogui.hotkey(*keys)
    except Exception as e:
        return {"status": "error", "error": str(e)}
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=HOST, port=PORT, reload=False)
