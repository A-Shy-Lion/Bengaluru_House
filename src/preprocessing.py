"""Utilities for cleaning and encoding the Bengaluru house price dataset."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np
import pandas as pd


def _convert_sqft(value: str) -> float | None:
    """Convert the mixed-format sqft field to a numeric value."""
    if not isinstance(value, str):
        return float(value) if pd.notna(value) else None

    tokens = value.split("-")
    if len(tokens) == 2:
        low, high = tokens
        try:
            return (float(low) + float(high)) / 2.0
        except ValueError:
            return None

    try:
        return float(value)
    except ValueError:
        return None


def _bhk_from_size(size_value: str) -> int:
    """Extract the numeric BHK value from the 'size' column."""
    try:
        return int(str(size_value).split(" ")[0])
    except (ValueError, AttributeError, IndexError):
        return 0


@dataclass
class BengaluruPreprocessor:
    """
    Reusable preprocessing pipeline that mirrors the notebook steps.

    It handles cleaning, outlier filtering, and one-hot encoding of locations.
    """

    rare_location_threshold: int = 10
    location_categories: List[str] = field(default_factory=list)
    feature_columns: List[str] = field(default_factory=list)

    def load_raw(self, csv_path: str) -> pd.DataFrame:
        return pd.read_csv(csv_path)

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply the same feature engineering and outlier removal as the notebook."""
        work_df = df.copy()
        work_df.drop(["area_type", "availability", "balcony", "society"], axis=1, errors="ignore", inplace=True)
        work_df.dropna(inplace=True)

        work_df["BHK"] = work_df["size"].apply(_bhk_from_size)
        work_df = work_df[work_df["BHK"] > 0]
        work_df["total_sqft"] = work_df["total_sqft"].apply(_convert_sqft)
        work_df.dropna(subset=["total_sqft"], inplace=True)

        work_df["price_per_sqft"] = work_df["price"] * 1_000_000 / work_df["total_sqft"]
        work_df["location"] = work_df["location"].astype(str).str.strip()

        work_df = self._bucket_locations(work_df)
        work_df = work_df[~(work_df["total_sqft"] / work_df["BHK"] < 300)]
        work_df = self._remove_pps_outliers(work_df)
        work_df = self._remove_bhk_outliers(work_df)
        work_df = work_df[work_df["bath"] < work_df["BHK"] + 2]

        return work_df

    def fit_transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Clean the dataset and return model-ready features and targets."""
        cleaned = self.clean_dataframe(df)
        self.location_categories = sorted([loc for loc in cleaned["location"].unique() if loc != "other"])
        X, y = self._build_features(cleaned)
        self.feature_columns = list(X.columns)
        return X, y

    def transform_input(self, *, location: str, total_sqft: float, bath: int, bhk: int) -> pd.DataFrame:
        """
        Prepare a single-row feature frame for inference using the learned location columns.
        Unknown locations are mapped to the 'other' bucket, which becomes all-zero dummies.
        """
        if not self.feature_columns:
            raise ValueError("Preprocessor has not been fit; train before predicting.")

        base = pd.DataFrame(
            [{"total_sqft": float(total_sqft), "bath": int(bath), "BHK": int(bhk)}]
        )
        dummies = pd.DataFrame(0, index=base.index, columns=self.location_categories)
        if location.strip() in self.location_categories:
            dummies.loc[base.index, location.strip()] = 1

        features = pd.concat([base, dummies], axis=1)
        return features.reindex(columns=self.feature_columns, fill_value=0)

    def _bucket_locations(self, df: pd.DataFrame) -> pd.DataFrame:
        counts = df["location"].value_counts()
        frequent = counts[counts > self.rare_location_threshold].index
        df["location"] = df["location"].apply(lambda loc: loc if loc in frequent else "other")
        return df

    def _remove_pps_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        filtered = pd.DataFrame()
        for _, group in df.groupby("location"):
            mean_pps = np.mean(group.price_per_sqft)
            std_pps = np.std(group.price_per_sqft)
            within_range = group[
                (group.price_per_sqft > (mean_pps - std_pps))
                & (group.price_per_sqft < (mean_pps + std_pps))
            ]
            filtered = pd.concat([filtered, within_range], ignore_index=True)
        return filtered

    def _remove_bhk_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        indices_to_drop: List[int] = []
        for _, location_df in df.groupby("location"):
            stats = {
                bhk: {
                    "mean": np.mean(bhk_df.price_per_sqft),
                    "std": np.std(bhk_df.price_per_sqft),
                    "count": bhk_df.shape[0],
                }
                for bhk, bhk_df in location_df.groupby("BHK")
            }

            for bhk, bhk_df in location_df.groupby("BHK"):
                smaller_bhk_stats = stats.get(bhk - 1)
                if smaller_bhk_stats and smaller_bhk_stats["count"] > 5:
                    bad_index = bhk_df[bhk_df.price_per_sqft < smaller_bhk_stats["mean"]].index
                    indices_to_drop.extend(bad_index)

        return df.drop(indices_to_drop, axis="index")

    def _build_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        features = df.drop(columns=["size", "price_per_sqft", "price"])
        y = df["price"].reset_index(drop=True)

        location_dummies = pd.get_dummies(features.pop("location"))
        if "other" in location_dummies.columns:
            location_dummies.drop(columns=["other"], inplace=True)

        # Guarantee consistent dummy columns
        for loc in self.location_categories:
            if loc not in location_dummies.columns:
                location_dummies[loc] = 0
        location_dummies = location_dummies[self.location_categories]

        X = pd.concat([features.reset_index(drop=True), location_dummies.reset_index(drop=True)], axis=1)
        return X, y
