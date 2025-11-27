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
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "5000"))
    ui_host = os.getenv("UI_HOST", "0.0.0.0")
    ui_port = int(os.getenv("UI_PORT", os.getenv("STREAMLIT_PORT", "5001")))

    if ui_port == api_port:
        ui_port += 1
        print(f"UI port trung v?i API, chuy?n sang {ui_port}")

    os.environ.setdefault("FRONTEND_URL", f"http://localhost:{ui_port}")
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
