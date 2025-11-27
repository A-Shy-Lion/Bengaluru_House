"""Prediction helpers for trained Bengaluru house price models."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import joblib

from src.preprocessing import BengaluruPreprocessor


def load_model_bundle(model_path: str | Path, preprocessor_path: str | Path) -> Tuple[object, BengaluruPreprocessor]:
    model = joblib.load(model_path)
    preprocessor: BengaluruPreprocessor = joblib.load(preprocessor_path)
    return model, preprocessor


def predict_price(
    model,
    preprocessor: BengaluruPreprocessor,
    *,
    location: str,
    total_sqft: float,
    bath: int,
    bhk: int,
) -> float:
    """Run a single prediction given raw feature values."""
    features = preprocessor.transform_input(
        location=location,
        total_sqft=total_sqft,
        bath=bath,
        bhk=bhk,
    )
    return float(model.predict(features)[0])


if __name__ == "__main__":
    # Example quickstart for manual testing.
    model_file = Path("../models/linear_regression.pkl")
    preprocessor_file = Path("../models/preprocessor.pkl")
    if model_file.exists() and preprocessor_file.exists():
        model, preprocessor = load_model_bundle(model_file, preprocessor_file)
        sample_price = predict_price(
            model,
            preprocessor,
            location="Whitefield",
            total_sqft=1200,
            bath=2,
            bhk=2,
        )
        print(f"Estimated price (lakhs): {sample_price:.2f}")
    else:
        print("Trained artifacts not found. Run training before predicting.")
