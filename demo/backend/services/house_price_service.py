from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Optional

import joblib

# Ensure the project root and src directory are on sys.path so imports work when
# running from the backend directory, and so joblib can resolve pickled objects
# that reference the bare "preprocessing" module.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
for p in (PROJECT_ROOT, SRC_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    preprocessing_module = importlib.import_module("src.preprocessing")
    # Provide a backward-compatible module name in case artifacts were pickled
    # when the module was imported as `preprocessing` instead of `src.preprocessing`.
    sys.modules.setdefault("preprocessing", preprocessing_module)
    from src.preprocessing import BengaluruPreprocessor  # noqa: F401
except Exception:
    # If import fails, joblib loading will raise later with a clearer message.
    BengaluruPreprocessor = None  # type: ignore


class HousePriceService:
    def __init__(
        self,
        model_path: Optional[Path | str] = None,
        preprocessor_path: Optional[Path | str] = None,
    ) -> None:
        default_preprocessor = PROJECT_ROOT / "models" / "preprocessor.pkl"
        self.model_path = Path(model_path) if model_path else None
        self.preprocessor_path = Path(preprocessor_path) if preprocessor_path else default_preprocessor
        self._model = None
        self._preprocessor = None

    def _resolve_paths(self) -> None:
        if self.model_path is None:
            model_name = os.getenv("HOUSE_MODEL_FILENAME") or "linear_regression_BengaluruHouse.pkl"
            self.model_path = PROJECT_ROOT / "models" / model_name

    def _load(self) -> None:
        self._resolve_paths()
        if self._model is None:
            if not self.model_path.exists():
                raise FileNotFoundError(f"Khong tim thay model tai {self.model_path}")
            self._model = joblib.load(self.model_path)
        if self._preprocessor is None:
            if not self.preprocessor_path.exists():
                raise FileNotFoundError(f"Khong tim thay preprocessor tai {self.preprocessor_path}")
            self._preprocessor = joblib.load(self.preprocessor_path)

    def predict(self, *, location: str, total_sqft: float, bath: int, bhk: int) -> float:
        self._load()
        features = self._preprocessor.transform_input(
            location=location,
            total_sqft=total_sqft,
            bath=bath,
            bhk=bhk,
        )
        price = float(self._model.predict(features)[0])
        return price


house_price_service = HousePriceService()
