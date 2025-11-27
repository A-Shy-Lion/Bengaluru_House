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

    def list_records(self) -> List[Dict[str, object]]:
        with self._lock:
            return list(self._read())


conversation_store = LocalConversationStore(Path(__file__).resolve().parent / "conversations.json")
house_store = LocalHouseStore(Path(__file__).resolve().parent / "houses.json")
