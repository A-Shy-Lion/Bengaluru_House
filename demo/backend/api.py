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
    history_path = ROOT_DIR / "demo" / "backend" / "storage" / "houses.json"
    metrics_path = ROOT_DIR / "models" / "metrics.json"
    if not data_path.exists():
        raise FileNotFoundError(f"Khong tim thay data tai {data_path}")

    trainer = ModelTrainer()
    models, metrics = trainer.train_models(str(data_path), history_path=history_path)
    best_name = trainer.select_best_model(metrics)
    best_metric = metrics[best_name]
    saved_metrics = trainer.load_saved_metrics(metrics_path)
    should_save = trainer.should_replace_model(best_metric, saved_metrics)

    old_rmse = None
    old_cv_r2 = None
    if saved_metrics and isinstance(saved_metrics.get("metrics"), dict):
        try:
            old_rmse = float(saved_metrics["metrics"].get("rmse"))
        except (TypeError, ValueError):
            old_rmse = None
        try:
            old_cv_r2 = (
                float(saved_metrics["metrics"].get("cv_r2"))
                if saved_metrics["metrics"].get("cv_r2") is not None
                else None
            )
        except (TypeError, ValueError):
            old_cv_r2 = None

    best_file: str | None = None
    if should_save:
        best_file = trainer.save_artifacts(
            models,
            metrics,
            model_dir=ROOT_DIR / "models",
            best_name=best_name,
        )
        trainer.save_metrics_file(
            metrics_path=metrics_path,
            model_name=best_name,
            model_filename=best_file,
            metrics=best_metric,
            train_rows=trainer.last_training_rows,
            history_rows=trainer.history_rows_used,
        )
        os.environ["HOUSE_MODEL_FILENAME"] = best_file
        print("Updated model, RMSE improved")
    else:
        best_file = (saved_metrics or {}).get("model_filename")
        # Keep env var aligned with the model we decided to keep.
        if best_file:
            os.environ["HOUSE_MODEL_FILENAME"] = best_file
        print("Model not improved, keep old one")

    if not best_file:
        best_file = os.getenv("HOUSE_MODEL_FILENAME") or "linear_regression_BengaluruHouse.pkl"
    os.environ.setdefault("HOUSE_MODEL_FILENAME", best_file)

    # Xay dung danh sach location theo tan suat va luu vao storage cho frontend/backend.
    if should_save and trainer.latest_training_df is not None:
        counts = trainer.latest_training_df["location"].value_counts()
        locations_payload = [
            {"name": name, "count": int(count)}
            for name, count in counts.items()
            if name != "other"
        ]
        location_service.save_locations(locations_payload)

    # In ket qua huan luyen ra console de de quan sat.
    print(
        f"Training rows={trainer.last_training_rows}, "
        f"history_used={trainer.history_rows_used}, "
        f"CV_R2_old={old_cv_r2 if old_cv_r2 is not None else 'n/a'}, "
        f"CV_R2_new={best_metric.cv_r2 if best_metric.cv_r2 is not None else 'n/a'}"
    )
    for name, metric in metrics.items():
        cv_display = f"{metric.cv_r2:.3f}" if metric.cv_r2 is not None else "n/a"
        print(
            f"{name}: RMSE={metric.rmse:.2f}, "
            f"MAPE={metric.mape:.2f}, CV_R2={cv_display}"
        )
    print(f"Best model candidate: {best_name}")
    return best_file or ""


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
