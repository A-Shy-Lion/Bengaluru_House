from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, redirect
from flask_cors import CORS

# Ensure project root on sys.path for absolute imports when running as a script
ROOT_DIR = Path(__file__).resolve().parents[2]
DEMO_DIR = Path(__file__).resolve().parents[1]
for p in (ROOT_DIR, DEMO_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Load environment variables from project root and local backend .env
load_dotenv(ROOT_DIR / ".env")
load_dotenv(DEMO_DIR / ".env", override=True)
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

from backend.services.location_service import location_service


_TRAINING_DONE = False


def _run_model_training() -> str:
    """
    Train models before starting the API. Ensures fresh artifacts exist and
    records the chosen model filename in env for downstream services.
    """
    from src.modeling import ModelTrainer

    data_path = ROOT_DIR / "data" / "Bengaluru_House_Data.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Khong tim thay data tai {data_path}")

    trainer = ModelTrainer()
    models, metrics = trainer.train_models(str(data_path))
    best_file = trainer.save_artifacts(models, metrics, model_dir=ROOT_DIR / "models")
    # Cho HousePriceService biet model nao da duoc luu.
    os.environ["HOUSE_MODEL_FILENAME"] = best_file

    # Xay dung danh sach location theo tan suat va luu vao storage cho frontend/backend.
    df_clean = trainer.preprocessor.clean_dataframe(trainer.preprocessor.load_raw(str(data_path)))
    counts = df_clean["location"].value_counts()
    locations_payload = [
        {"name": name, "count": int(count)}
        for name, count in counts.items()
        if name != "other"
    ]
    location_service.save_locations(locations_payload)

    # In ket qua huan luyen ra console de de quan sat.
    for name, metric in metrics.items():
        cv_display = f"{metric.cv_r2:.3f}" if metric.cv_r2 is not None else "n/a"
        print(
            f"{name}: RMSE={metric.rmse:.2f}, MAE={metric.mae:.2f}, "
            f"R2={metric.r2:.3f}, CV_R2={cv_display}"
        )
    print(f"Saved best model as: {best_file}")
    return best_file


from backend.routes.chat_routes import chat_bp


def create_app() -> Flask:
    global _TRAINING_DONE

    skip_training = os.getenv("SKIP_TRAINING_ON_START", "").lower() in ("1", "true", "yes")
    if not skip_training and not _TRAINING_DONE:
        best_model = _run_model_training()
        print(f"[startup] Train model thanh cong, dung file: {best_model}")
        _TRAINING_DONE = True
    elif skip_training:
        print("[startup] Bo qua train model (SKIP_TRAINING_ON_START=1).")

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
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
