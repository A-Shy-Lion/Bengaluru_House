from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, redirect
from flask_cors import CORS

# Load environment variables from project root and local backend .env
ROOT_DIR = Path(__file__).resolve().parents[2]
DEMO_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")
load_dotenv(DEMO_DIR / ".env", override=True)
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

from .routes.chat_routes import chat_bp


def create_app() -> Flask:
    app = Flask(__name__)
    # Allow all origins for local testing; tighten in prod.
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.register_blueprint(chat_bp)

    @app.route("/")
    def root():
        """
        Redirect tới frontend nếu có cấu hình FRONTEND_URL (hoặc RENDER_EXTERNAL_URL),
        ngược lại trả về thông báo JSON để tránh chuyển hướng về localhost trên môi trường deploy.
        """
        frontend_url = os.getenv("FRONTEND_URL") or os.getenv("RENDER_EXTERNAL_URL")
        if frontend_url:
            return redirect(frontend_url)
        return {"message": "Backend is running. Set FRONTEND_URL to enable redirect."}

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS"
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
