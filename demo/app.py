from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from werkzeug.serving import make_server

from backend.api import create_app


def start_flask(api_host: str, api_port: int):
    app = create_app()
    server = make_server(api_host, api_port, app)

    def _run():
        server.serve_forever()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return server


def start_streamlit(ui_host: str, ui_port: int) -> subprocess.Popen:
    ui_path = Path(__file__).parent / "frontend" / "ui.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ui_path),
        "--server.address",
        ui_host,
        "--server.port",
        str(ui_port),
        "--server.headless",
        "true",
    ]
    return subprocess.Popen(cmd)


def shutdown_process(proc: Optional[subprocess.Popen]) -> None:
    if proc is None:
        return
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main():
    api_host = os.getenv("API_HOST", "localhost")
    api_port = int(os.getenv("API_PORT", "10000"))
    ui_host = os.getenv("UI_HOST", "localhost")
    ui_port = int(os.getenv("UI_PORT", os.getenv("STREAMLIT_PORT", "10001")))

    if ui_port == api_port:
        ui_port += 1
        print(f"UI port trùng với API, chuyển sang {ui_port}")

    # Ưu tiên URL bên ngoài khi deploy (vd: Render). Nếu không có, chỉ đặt localhost cho môi trường dev.
    frontend_url = os.getenv("FRONTEND_URL") or os.getenv("RENDER_EXTERNAL_URL")
    if not frontend_url and ui_host in ("localhost", "127.0.0.1"):
        frontend_url = f"http://{ui_host}:{ui_port}"
    if frontend_url:
        os.environ["FRONTEND_URL"] = frontend_url

    print(f"Starting Flask API on http://{api_host}:{api_port}/api")
    api_server = start_flask(api_host, api_port)

    print(f"Starting Streamlit UI on http://{ui_host}:{ui_port}")
    ui_proc = start_streamlit(ui_host, ui_port)

    try:
        while ui_proc.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping servers...")
    finally:
        api_server.shutdown()
        shutdown_process(ui_proc)


if __name__ == "__main__":
    main()
