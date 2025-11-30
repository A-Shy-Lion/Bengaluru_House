"""Model training and evaluation utilities for the house price project."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import KFold, cross_val_score, train_test_split

from preprocessing import BengaluruPreprocessor


@dataclass
class ModelMetrics:
    rmse: float
    mape: float
    cv_r2: float | None = None

    def as_dict(self) -> Dict[str, float | None]:
        return {
            "rmse": float(self.rmse),
            "mape": float(self.mape),
            "cv_r2": None if self.cv_r2 is None else float(self.cv_r2),
        }


def _evaluate(model, X_test, y_test) -> ModelMetrics:
    preds = model.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    mape = float(np.mean(np.abs((y_test - preds) / y_test)) * 100)
    return ModelMetrics(rmse=rmse, mape=mape)


def _cross_val_r2(model, X_train, y_train, splits: int = 5) -> float:
    kf = KFold(n_splits=splits, shuffle=True, random_state=42)
    scores = cross_val_score(model, X_train, y_train, cv=kf, scoring="r2")
    return float(scores.mean())


class ModelTrainer:
    """Train and persist models following the notebook's workflow."""

    def __init__(self, test_size: float = 0.2, random_state: int = 42, rare_location_threshold: int = 10):
        self.test_size = test_size
        self.random_state = random_state
        self.preprocessor = BengaluruPreprocessor(rare_location_threshold=rare_location_threshold)
        self.history_rows_used: int = 0
        self.last_training_rows: int = 0
        self.latest_training_df: Optional[pd.DataFrame] = None

    def _load_history_training_data(self, history_path: Path) -> pd.DataFrame:
        """
        Load additional training rows from houses.json (prediction history).

        Rows with missing fields or non-numeric values are dropped to avoid
        crashing the preprocessing pipeline.
        """
        if not history_path.exists():
            return pd.DataFrame()

        try:
            raw = json.loads(history_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return pd.DataFrame()

        if not isinstance(raw, list):
            return pd.DataFrame()

        cleaned_rows = []
        for item in raw:
            location = item.get("location")
            total_sqft = item.get("total_sqft")
            bath = item.get("bath")
            bhk = item.get("bhk")
            price = item.get("predicted_price_lakh")

            if any(val in (None, "") for val in (location, total_sqft, bath, bhk, price)):
                continue

            try:
                total_sqft_val = float(total_sqft)
                bath_val = int(bath)
                bhk_val = int(bhk)
                price_val = float(price)
            except (TypeError, ValueError):
                continue

            if total_sqft_val <= 0 or bath_val <= 0 or bhk_val <= 0 or price_val <= 0:
                continue

            cleaned_rows.append(
                {
                    # Columns align with the raw CSV schema; unused ones are set to benign defaults.
                    "area_type": "Built-up  Area",
                    "availability": "Ready To Move",
                    "location": str(location).strip(),
                    "size": f"{bhk_val} BHK",
                    "society": None,
                    "total_sqft": total_sqft_val,
                    "bath": bath_val,
                    "balcony": None,
                    "price": price_val,
                }
            )

        return pd.DataFrame(cleaned_rows)

    def prepare_data(self, csv_path: str, history_path: str | Path | None = None) -> Tuple:
        df_raw = self.preprocessor.load_raw(csv_path)
        base_clean = self.preprocessor.clean_dataframe(df_raw)

        history_clean = pd.DataFrame()
        if history_path:
            history_raw = self._load_history_training_data(Path(history_path))
            if not history_raw.empty:
                history_clean = self.preprocessor.clean_dataframe(history_raw)

        combined_clean = pd.concat([base_clean, history_clean], ignore_index=True)

        self.history_rows_used = len(history_clean.index)
        self.latest_training_df = combined_clean
        X, y = self.preprocessor.fit_transform_cleaned(combined_clean)
        self.last_training_rows = len(y)
        return train_test_split(X, y, test_size=self.test_size, random_state=self.random_state)

    def train_models(
        self, csv_path: str, history_path: str | Path | None = None
    ) -> Tuple[Dict[str, object], Dict[str, ModelMetrics]]:
        X_train, X_test, y_train, y_test = self.prepare_data(csv_path, history_path=history_path)

        models = {
            "linear_regression": LinearRegression(),
            "random_forest": RandomForestRegressor(
                n_estimators=200, random_state=self.random_state, n_jobs=-1
            ),
        }

        metrics: Dict[str, ModelMetrics] = {}
        for name, model in models.items():
            model.fit(X_train, y_train)
            metrics[name] = _evaluate(model, X_test, y_test)
            metrics[name].cv_r2 = _cross_val_r2(model, X_train, y_train)

        return models, metrics

    def select_best_model(self, metrics: Dict[str, ModelMetrics]) -> str:
        """Pick the model with the best CV_R2 (fallback: lowest RMSE)."""

        def score(name: str) -> float:
            metric = metrics[name]
            if metric.cv_r2 is not None:
                return metric.cv_r2
            # Lower RMSE is better; invert to keep a single max() call.
            return -metric.rmse

        return max(metrics.keys(), key=score)

    def save_artifacts(
        self,
        models: Dict[str, object],
        metrics: Dict[str, ModelMetrics],
        model_dir: str | Path = "../models",
        preprocessor_name: str = "preprocessor.pkl",
        best_name: str | None = None,
    ) -> str:
        """
        Persist only the best model (by RMSE) with a `{model_name}_BengaluruHouse.pkl`
        filename. Always saves the preprocessor alongside for inference compatibility.
        """
        model_path = Path(model_dir)
        model_path.mkdir(parents=True, exist_ok=True)

        best_model_name = best_name or self.select_best_model(metrics)
        best_model = models[best_model_name]

        best_filename = f"{best_model_name}_BengaluruHouse.pkl"
        joblib.dump(best_model, model_path / best_filename)
        joblib.dump(self.preprocessor, model_path / preprocessor_name)

        return best_filename

    def _read_metrics_history(self, metrics_path: Path) -> list[Dict[str, object]]:
        if not metrics_path.exists():
            return []
        try:
            data = json.loads(metrics_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

        if isinstance(data, dict):
            if isinstance(data.get("history"), list):
                return [entry for entry in data["history"] if isinstance(entry, dict)]
            if "metrics" in data:
                # Backward compatibility for single-entry structure.
                return [data]
        if isinstance(data, list):
            return [entry for entry in data if isinstance(entry, dict)]
        return []

    def load_saved_metrics(self, metrics_path: str | Path) -> Optional[Dict[str, object]]:
        """
        Return the most recent metrics record saved in metrics.json (if any).
        Supports both legacy single-object and new history list format.
        """
        history = self._read_metrics_history(Path(metrics_path))
        if not history:
            return None
        latest = history[-1]
        metrics = latest.get("metrics")
        if not isinstance(metrics, dict) or "rmse" not in metrics:
            return None
        return latest

    def should_replace_model(self, new_metrics: ModelMetrics, saved_metrics: Optional[Dict[str, object]]) -> bool:
        if not saved_metrics:
            return True

        raw_metrics = saved_metrics.get("metrics", {}) if isinstance(saved_metrics, dict) else {}
        old_cv_r2: float | None
        old_rmse: float | None
        try:
            old_cv_r2 = float(raw_metrics.get("cv_r2")) if raw_metrics.get("cv_r2") is not None else None
        except (TypeError, ValueError):
            old_cv_r2 = None
        try:
            old_rmse = float(raw_metrics.get("rmse")) if raw_metrics.get("rmse") is not None else None
        except (TypeError, ValueError):
            old_rmse = None

        if new_metrics.cv_r2 is not None:
            if old_cv_r2 is None:
                return True
            return new_metrics.cv_r2 > old_cv_r2

        if old_rmse is None:
            return True
        return new_metrics.rmse < old_rmse

    def save_metrics_file(
        self,
        *,
        metrics_path: str | Path,
        model_name: str,
        model_filename: str,
        metrics: ModelMetrics,
        train_rows: int | None = None,
        history_rows: int | None = None,
    ) -> None:
        metrics_path = Path(metrics_path)
        payload: Dict[str, object] = {
            "model_name": model_name,
            "model_filename": model_filename,
            "metrics": metrics.as_dict(),
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
        if train_rows is not None:
            payload["train_rows"] = int(train_rows)
        if history_rows is not None:
            payload["history_rows"] = int(history_rows)

        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        history = self._read_metrics_history(metrics_path)
        history.append(payload)
        metrics_path.write_text(json.dumps({"history": history}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    data_path = Path("../data/Bengaluru_House_Data.csv")
    trainer = ModelTrainer()
    models, metrics = trainer.train_models(str(data_path))
    best_name = trainer.select_best_model(metrics)
    best_file = trainer.save_artifacts(models, metrics, best_name=best_name)

    for name, metric in metrics.items():
        cv_display = f"{metric.cv_r2:.3f}" if metric.cv_r2 is not None else "n/a"
        print(
            f"{name}: RMSE={metric.rmse:.2f}, "
            f"MAPE={metric.mape:.2f}, CV_R2={cv_display}"
        )
    print(f"Saved best model as: {best_file}")
