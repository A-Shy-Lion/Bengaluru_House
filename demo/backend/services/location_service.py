from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class LocationService:
    def _normalize_name(self, name: str) -> str:
        """Trim and collapse whitespace so lookups are resilient to spacing differences."""
        return " ".join(str(name).split()).strip()

    """
    Manage location options derived from the training dataset.

    Stores a JSON list sorted by popularity for reuse across API routes and UI.
    """

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        base_dir = Path(__file__).resolve().parents[1] / "storage"
        self.storage_path = storage_path or (base_dir / "locations.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def save_locations(self, locations: List[Dict[str, object]]) -> None:
        """
        Persist a list of dicts: {"name": str, "count": int}, sorted by count desc.
        """
        ordered = sorted(locations, key=lambda item: int(item.get("count", 0)), reverse=True)
        payload = {"locations": ordered}
        self.storage_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self) -> Dict[str, List[Dict[str, object]]]:
        if not self.storage_path.exists():
            return {"locations": []}
        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and isinstance(raw.get("locations"), list):
                return raw
        except (json.JSONDecodeError, OSError):
            pass
        return {"locations": []}

    def get_locations(self) -> List[Dict[str, object]]:
        """
        Return normalized, de-duplicated locations sorted by count desc.
        Names are normalized to avoid double-space/casing glitches in raw data.
        """
        data = self._load()
        merged: Dict[str, Dict[str, object]] = {}
        for item in data.get("locations", []):
            name = self._normalize_name(item.get("name", ""))
            if not name:
                continue
            try:
                count = int(item.get("count", 0))
            except (TypeError, ValueError):
                count = 0
            existing = merged.get(name)
            if existing:
                existing["count"] = max(int(existing.get("count", 0)), count)
            else:
                merged[name] = {"name": name, "count": count}

        return sorted(merged.values(), key=lambda item: int(item.get("count", 0)), reverse=True)

    def get_location_names(self) -> List[str]:
        return [self._normalize_name(item.get("name", "")) for item in self.get_locations() if item.get("name")]

    def get_lookup(self) -> Dict[str, str]:
        """Lowercase lookup mapping for validation."""
        return {name.lower(): name for name in self.get_location_names()}

    def detect_in_text(self, text: str) -> Optional[str]:
        """
        Return the first canonical location name found as a substring of the text.
        Picks the longest matching name to reduce false positives on short overlaps.
        """
        if not text:
            return None
        names = self.get_location_names()
        lookup = self.get_lookup()
        normalized_text = " ".join(text.lower().split())
        matches = [name for name in names if name and name.lower() in normalized_text]
        if not matches:
            return None
        best = max(matches, key=len)
        return lookup.get(best.lower(), best)

    def canonicalize(self, location: str) -> Optional[str]:
        """
        Return the canonical location name if it exists in the saved list,
        otherwise None.
        """
        if not location:
            return None
        lookup = self.get_lookup()
        return lookup.get(self._normalize_name(location).lower())


location_service = LocationService()
