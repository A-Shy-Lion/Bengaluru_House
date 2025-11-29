from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional
from uuid import uuid4


class LocalConversationStore:
    """
    Simple JSON file-based storage to persist chat history locally.
    Not built for high write throughput but sufficient for local/dev use.
    """

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        if not self.storage_path.exists():
            self._write({})

    def new_session(self) -> str:
        return uuid4().hex

    def _read(self) -> Dict[str, List[Dict[str, str]]]:
        if not self.storage_path.exists():
            return {}
        try:
            return json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _write(self, data: Dict[str, List[Dict[str, str]]]) -> None:
        self.storage_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        with self._lock:
            data = self._read()
            return list(data.get(session_id, []))

    def save_history(self, session_id: str, history: List[Dict[str, str]]) -> None:
        with self._lock:
            data = self._read()
            data[session_id] = history
            self._write(data)

# Simple file-based store for Bengaluru_House style records.
class LocalHouseStore:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        if not self.storage_path.exists():
            self._write([])

    def _read(self) -> List[Dict[str, object]]:
        if not self.storage_path.exists():
            return []
        try:
            return json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _write(self, data: List[Dict[str, object]]) -> None:
        self.storage_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_record(
        self,
        *,
        location: str,
        total_sqft: float,
        bath: int,
        bhk: int,
        predicted_price_lakh: Optional[float] = None,
        source: str = "api",
    ) -> Dict[str, object]:
        record = {
            "id": uuid4().hex,
            "location": location,
            "total_sqft": float(total_sqft),
            "bath": int(bath),
            "bhk": int(bhk),
            "predicted_price_lakh": None if predicted_price_lakh is None else float(predicted_price_lakh),
            "source": source,
        }
        with self._lock:
            data = self._read()
            data.append(record)
            self._write(data)
        return record

    def get_record_by_session(self, session_id: str) -> Optional[Dict[str, object]]:
        """Return a copy of the first record tied to this session id, if any."""
        with self._lock:
            for item in self._read():
                if item.get("session_id") == session_id:
                    return dict(item)
        return None

    def upsert_session_record(
        self,
        session_id: str,
        *,
        location: Optional[str] = None,
        total_sqft: Optional[float | int | str] = None,
        bath: Optional[int | str] = None,
        bhk: Optional[int | str] = None,
        predicted_price_lakh: Optional[float] = None,
        source: str = "chat",
    ) -> Dict[str, object]:
        """
        Create or update a per-session record with partial fields.
        Values are kept even if not all inputs are present yet.
        """

        def _maybe_float(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return val

        def _maybe_int(val):
            try:
                return int(val)
            except (TypeError, ValueError):
                return val

        with self._lock:
            data = self._read()
            existing = next((r for r in data if r.get("session_id") == session_id), None)
            if existing is None:
                record = {
                    "id": uuid4().hex,
                    "session_id": session_id,
                    "location": location,
                    "total_sqft": _maybe_float(total_sqft) if total_sqft is not None else None,
                    "bath": _maybe_int(bath) if bath is not None else None,
                    "bhk": _maybe_int(bhk) if bhk is not None else None,
                    "predicted_price_lakh": None if predicted_price_lakh is None else float(predicted_price_lakh),
                    "source": source,
                }
                data.append(record)
                self._write(data)
                return record

            if location is not None:
                existing["location"] = location
            if total_sqft is not None:
                existing["total_sqft"] = _maybe_float(total_sqft)
            if bath is not None:
                existing["bath"] = _maybe_int(bath)
            if bhk is not None:
                existing["bhk"] = _maybe_int(bhk)
            if predicted_price_lakh is not None:
                existing["predicted_price_lakh"] = float(predicted_price_lakh)
            if source:
                existing["source"] = source

            self._write(data)
            return existing

    def list_records(self) -> List[Dict[str, object]]:
        with self._lock:
            return list(self._read())


conversation_store = LocalConversationStore(Path(__file__).resolve().parent / "conversations.json")
house_store = LocalHouseStore(Path(__file__).resolve().parent / "houses.json")
