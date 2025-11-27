"""Model training and evaluation utilities for the house price project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split

from preprocessing import BengaluruPreprocessor


@dataclass
class ModelMetrics:
    mae: float
    rmse: float
    r2: float
    mape: float
    cv_r2: float | None = None


def _evaluate(model, X_test, y_test) -> ModelMetrics:
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    r2 = r2_score(y_test, preds)
    mape = float(np.mean(np.abs((y_test - preds) / y_test)) * 100)
    return ModelMetrics(mae=mae, rmse=rmse, r2=r2, mape=mape)


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

    def prepare_data(self, csv_path: str) -> Tuple:
        df_raw = self.preprocessor.load_raw(csv_path)
        X, y = self.preprocessor.fit_transform(df_raw)
        return train_test_split(X, y, test_size=self.test_size, random_state=self.random_state)

    def train_models(self, csv_path: str) -> Tuple[Dict[str, object], Dict[str, ModelMetrics]]:
        X_train, X_test, y_train, y_test = self.prepare_data(csv_path)

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

    def save_artifacts(
        self,
        models: Dict[str, object],
        metrics: Dict[str, ModelMetrics],
        model_dir: str | Path = "../models",
        preprocessor_name: str = "preprocessor.pkl",
    ) -> str:
        """
        Persist only the best model (by CV R², fallback to plain R²) with a
        `{model_name}_BengaluruHouse.pkl` filename. Always saves the preprocessor
        alongside for inference compatibility.
        """
        model_path = Path(model_dir)
        model_path.mkdir(parents=True, exist_ok=True)

        def score(name: str) -> float:
            metric = metrics[name]
            return metric.cv_r2 if metric.cv_r2 is not None else metric.r2

        best_name = max(models.keys(), key=score)
        best_model = models[best_name]

        best_filename = f"{best_name}_BengaluruHouse.pkl"
        joblib.dump(best_model, model_path / best_filename)
        joblib.dump(self.preprocessor, model_path / preprocessor_name)

        return best_filename


if __name__ == "__main__":
    data_path = Path("../data/Bengaluru_House_Data.csv")
    trainer = ModelTrainer()
    models, metrics = trainer.train_models(str(data_path))
    best_file = trainer.save_artifacts(models, metrics)

    for name, metric in metrics.items():
        cv_display = f"{metric.cv_r2:.3f}" if metric.cv_r2 is not None else "n/a"
        print(
            f"{name}: RMSE={metric.rmse:.2f}, MAE={metric.mae:.2f}, "
            f"R2={metric.r2:.3f}, CV_R2={cv_display}"
        )
    print(f"Saved best model as: {best_file}")
