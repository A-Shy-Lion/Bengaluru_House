from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

# Prefer explicit API_BASE_URL env; fallback to localhost:10000/api (port backend đang chạy).
DEFAULT_API_BASE = os.getenv("API_BASE_URL", "http://localhost:10000/api")


@dataclass
class ChatResponse:
    session_id: str
    reply: str
    history: List[Dict[str, Any]]
    detected_fields: Dict[str, Any]
    prediction: Optional[float] = None


class ApiClient:
    """Thin wrapper gọi API Flask /api/*."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or DEFAULT_API_BASE).rstrip("/")

    def _handle_response(self, resp: requests.Response) -> Dict[str, Any]:
        try:
            data = resp.json()
        except Exception:
            resp.raise_for_status()
            return {}
        if not resp.ok:
            raise RuntimeError(data.get("error") or resp.text)
        return data

    def chat(self, message: str, session_id: Optional[str] = None) -> ChatResponse:
        payload: Dict[str, Any] = {"message": message}
        if session_id:
            payload["session_id"] = session_id
        resp = requests.post(f"{self.base_url}/chat", json=payload, timeout=20)
        data = self._handle_response(resp)
        return ChatResponse(
            session_id=data.get("session_id", session_id or ""),
            reply=data.get("reply", ""),
            history=data.get("history") or [],
            detected_fields=data.get("detected_fields") or {},
            prediction=data.get("prediction"),
        )

    def fetch_history(self, session_id: str) -> ChatResponse:
        resp = requests.get(f"{self.base_url}/chat/{session_id}", timeout=10)
        data = self._handle_response(resp)
        return ChatResponse(
            session_id=data.get("session_id", session_id),
            reply=data.get("reply", ""),
            history=data.get("history") or [],
            detected_fields=data.get("detected_fields") or {},
            prediction=data.get("prediction"),
        )
