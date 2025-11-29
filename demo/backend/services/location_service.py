from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class LocationService:
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
        data = self._load()
        return data.get("locations", [])

    def get_location_names(self) -> List[str]:
        return [str(item.get("name", "")).strip() for item in self.get_locations() if item.get("name")]

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
        lowered = text.lower()
        matches = [name for name in names if name and name.lower() in lowered]
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
        return lookup.get(location.strip().lower())


location_service = LocationService()
