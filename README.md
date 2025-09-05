# Remote Access MVP (LAN-only)

**What it is:** a tiny proof-of-concept that streams your screen as MJPEG over HTTP and sends mouse/keyboard events via WebSocket.

**What it's not:** a hardened, internet-ready remote desktop. Start on your LAN only.

## Install (on the HOST you want to control)
1. Install Python 3.10+.
2. In a terminal:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   set RA_TOKEN=JimmyJohnsisTheBest
   set RA_FPS=12
   set RA_SCALE=0.7
   python server.py
   ```
   (On PowerShell use `$env:RA_TOKEN="make-a-strong-one"`)

3. The server listens on `0.0.0.0:8765` by default. You can change port: `set RA_PORT=9000`.

## Use (from the CLIENT machine)
- Open `client.html` in a browser.
- Enter the host's LAN IP and port (e.g., `192.168.1.23:8765`) and the same token.
- Click **Connect**. You should see the screen. Click/drag/type to control.

## Tips
- If the image is laggy, lower `RA_FPS`, `RA_SCALE`, or `RA_QUALITY` on the host.
- Multi-monitor: it currently captures the *virtual* full screen. You can change `monitor = sct.monitors[0]` to `1`, `2`, etc.
- Keyboard: OS-secured combos like Ctrl+Alt+Del cannot be synthesized by userland apps.

## Security & Scope
- **Only run this on machines you own and networks you trust.**
- **Always set `RA_TOKEN`** to a long random string. The client must provide it.
- By design this is HTTP (no TLS). For WAN access you must add TLS + proper auth + NAT traversal (e.g., Cloudflare Tunnel, Tailscale, or a TURN server if you switch to WebRTC).
- Consider a service wrapper so it runs on startup (Task Scheduler on Windows).

## Next steps (upgrade path)
- Swap MJPEG for WebRTC (near‑real‑time, adaptive bitrate).
- Add clipboard sync and file transfer (HTTP endpoint + auth).
- Switch to per-session, expiring tokens and rate limiting.
- Optional: build in Rust or Go for lower latency and a single-file binary.
"# remote-access-mvp" 
"# remote-access-mvp" 
