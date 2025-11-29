from __future__ import annotations

import asyncio
from flask import Blueprint, jsonify, request

from backend.services.llm_service import llm_service
from backend.services.house_price_service import house_price_service
from backend.services.location_service import location_service
from backend.storage.local_storage import conversation_store, house_store

chat_bp = Blueprint("chat", __name__)


def _extract_fields(
    text: str,
    *,
    allowed_lookup: dict[str, str] | None = None,
    allowed_names: list[str] | None = None,
) -> dict:
    """
    Extract house-price fields from arbitrary text, with optional validation
    against allowed locations and a substring fallback for known names.
    """
    if not text:
        return {}
    import re

    def _normalize_location(val: str) -> str:
        return " ".join(val.split()).strip().lower()

    def _clean_number(val: str) -> str:
        cleaned = re.sub(r"[^\d\.]", "", val.replace(",", ""))
        return cleaned.rstrip(".")

    found: dict[str, str] = {}

    # Location patterns
    for pattern in (
        r"\blocation\s*[:=]\s*([^\n,;]+)",
        r"\bkhu\s*v[uu]c\s*[:=]?\s*([^\n,;]+)",
        r"\b(?:o|ở|tai|tại|in)\s+([^\n,;]+)",
    ):
        m = re.search(pattern, text, re.IGNORECASE)
        if m and m.group(1):
            candidate = m.group(1).strip()
            if allowed_lookup is None:
                found["location"] = candidate
            else:
                canonical = allowed_lookup.get(_normalize_location(candidate))
                if canonical:
                    found["location"] = canonical
            break

    # Fallback: substring search any known location name in text
    if "location" not in found and allowed_names:
        lowered = " ".join(text.lower().split())
        matches = [name for name in allowed_names if name and name.lower() in lowered]
        if matches:
            best = max(matches, key=len)
            found["location"] = allowed_lookup.get(best.lower(), best) if allowed_lookup else best

    # total_sqft patterns (allow commas/decimals and unit mentions)
    for pattern in (
        r"\btotal[_\s]*sqft\s*[:=]?\s*([\d,\.]+)",
        r"([\d,\.]+)\s*(sqft|ft2|feet\s*squared)",
    ):
        m = re.search(pattern, text, re.IGNORECASE)
        if m and m.group(1):
            found["total_sqft"] = _clean_number(m.group(1))
            break

    # bath patterns
    for pattern in (
        r"\bbath(?:room|s)?\s*[:=]?\s*([\d,\.]+)",
        r"\bwc\b\s*[:=]?\s*([\d,\.]+)",
    ):
        m = re.search(pattern, text, re.IGNORECASE)
        if m and m.group(1):
            found["bath"] = _clean_number(m.group(1))
            break

    # bhk patterns (capture both 'bhk 3' and '3 bhk')
    for pattern in (
        r"\bbhk\b\s*[:=]?\s*([\d,\.]+)",
        r"([\d,\.]+)\s*bhk\b",
    ):
        m = re.search(pattern, text, re.IGNORECASE)
        if m and m.group(1):
            found["bhk"] = _clean_number(m.group(1))
            break

    return found


def _merge_fields_from_history(
    history: list[dict],
    *,
    allowed_lookup: dict[str, str] | None = None,
    allowed_names: list[str] | None = None,
) -> dict:
    """Walk through conversation messages in order and keep latest seen values."""
    merged: dict[str, str] = {}
    for msg in history:
        content = msg.get("content", "")
        merged.update(_extract_fields(content, allowed_lookup=allowed_lookup, allowed_names=allowed_names))
    return merged


def _has_full_fields(fields: dict) -> bool:
    required = {"location", "total_sqft", "bath", "bhk"}
    return required.issubset({k for k, v in fields.items() if v not in (None, "")})


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    user_message = (payload.get("message") or "").strip()
    session_id = (payload.get("session_id") or "").strip() or conversation_store.new_session()
    allowed_lookup = location_service.get_lookup()
    allowed_names = location_service.get_location_names()
    # luôn mặc định tiếng Việt

    if not user_message:
        return jsonify({"error": "Thiếu 'message' từ người dùng"}), 400

    history = conversation_store.get_history(session_id)
    history.append({"role": "user", "content": user_message})

    raw_fields = _extract_fields(user_message)
    canonical_fields = _extract_fields(user_message, allowed_lookup=allowed_lookup, allowed_names=allowed_names)
    if not canonical_fields.get("location"):
        inferred_loc = location_service.detect_in_text(user_message)
        if inferred_loc:
            canonical_fields["location"] = inferred_loc
            raw_fields.setdefault("location", inferred_loc)

    detected_fields = _merge_fields_from_history(
        history, allowed_lookup=allowed_lookup, allowed_names=allowed_names
    )
    # Ưu tiên giá trị đã chuẩn hóa của lượt hiện tại.
    for key, val in canonical_fields.items():
        if val:
            detected_fields[key] = val

    # Kết hợp với dữ liệu đã lưu trong houses.json (nếu có).
    existing_house = house_store.get_record_by_session(session_id)
    if existing_house:
        for field in ("location", "total_sqft", "bath", "bhk"):
            if detected_fields.get(field) in (None, "") and existing_house.get(field) not in (None, ""):
                detected_fields[field] = existing_house.get(field)

    # Lưu lại mọi trường đã biết (kể cả thiếu).
    persisted_house = house_store.upsert_session_record(
        session_id,
        location=detected_fields.get("location"),
        total_sqft=detected_fields.get("total_sqft"),
        bath=detected_fields.get("bath"),
        bhk=detected_fields.get("bhk"),
        source="chat",
    )
    # Đồng bộ detected_fields với bản lưu để trả về client.
    for field in ("location", "total_sqft", "bath", "bhk"):
        detected_fields[field] = persisted_house.get(field)

    if raw_fields.get("location") and not canonical_fields.get("location"):
        reply = "Mô hình hiện không hỗ trợ khu vực đó. Vui lòng chọn một location hợp lệ trong danh sách."
        history.append({"role": "assistant", "content": reply})
        conversation_store.save_history(session_id, history)
        return jsonify(
            {
                "session_id": session_id,
                "reply": reply,
                "history": history,
                "detected_fields": detected_fields,
                "prediction": None,
            }
        )

    prediction_val = None
    extra_messages = []
    missing_fields = [f for f in ("location", "total_sqft", "bath", "bhk") if detected_fields.get(f) in (None, "")]

    if not missing_fields:
        try:
            total_sqft_val = float(detected_fields["total_sqft"])
            bath_val = int(detected_fields["bath"])
            bhk_val = int(detected_fields["bhk"])
            ready_for_prediction = True
        except (ValueError, TypeError):
            ready_for_prediction = False
            extra_messages.append(
                {
                    "role": "assistant",
                    "content": "[Thiếu/không hợp lệ] Vui lòng cung cấp số hợp lệ cho total_sqft, bath, bhk để dự đoán.",
                }
            )
        if ready_for_prediction:
            try:
                prediction_val = house_price_service.predict(
                    location=detected_fields["location"],
                    total_sqft=total_sqft_val,
                    bath=bath_val,
                    bhk=bhk_val,
                )
                # Lưu lại đầu vào/kết quả vào local storage (cập nhật record session).
                persisted_house = house_store.upsert_session_record(
                    session_id,
                    location=detected_fields["location"],
                    total_sqft=total_sqft_val,
                    bath=bath_val,
                    bhk=bhk_val,
                    predicted_price_lakh=prediction_val,
                    source="chat",
                )
                detected_fields.update({k: persisted_house.get(k) for k in ("location", "total_sqft", "bath", "bhk")})
                # Provide a hidden assistant message so LLM can phrase the answer with the model result.
                extra_messages.append(
                    {
                        "role": "assistant",
                        "content": (
                            f"[Kết quả mô hình] location={detected_fields['location']}, "
                            f"total_sqft={detected_fields['total_sqft']}, "
                            f"bath={detected_fields['bath']}, "
                            f"bhk={detected_fields['bhk']}, "
                            f"giá dự đoán (lakh)={prediction_val:.2f}."
                        ),
                    }
                )
                extra_messages.append(
                    {
                        "role": "user",
                        "content": "Hãy báo kết quả dự đoán trên cho người dùng bằng tiếng Việt, kèm giải thích ngắn gọn.",
                    }
                )
            except Exception as exc:  # pragma: no cover - runtime safety
                extra_messages.append(
                    {
                        "role": "assistant",
                        "content": f"[Lỗi dự đoán] Không thể chạy mô hình: {exc}",
                    }
                )
    else:
        extra_messages.append(
            {
                "role": "assistant",
                "content": f"[Thiếu thông tin] Còn thiếu: {', '.join(missing_fields)}. "
                "Hãy hỏi người dùng bổ sung trước khi dự đoán.",
            }
        )

    try:
        reply = asyncio.run(llm_service.chat(history + extra_messages))
    except Exception as exc:  # pragma: no cover - runtime safety
        return jsonify({"error": f"Không gọi được LLM: {exc}"}), 500

    history.append({"role": "assistant", "content": reply})
    conversation_store.save_history(session_id, history)

    # Recompute detected fields including the assistant reply so the frontend can persist latest values.
    detected_fields = _merge_fields_from_history(
        history, allowed_lookup=allowed_lookup, allowed_names=allowed_names
    )

    return jsonify(
        {
            "session_id": session_id,
            "reply": reply,
            "history": history,
            "detected_fields": detected_fields,
            "prediction": prediction_val,
        }
    )


@chat_bp.route("/api/chat/<session_id>", methods=["GET"])
def get_history(session_id: str):
    allowed_lookup = location_service.get_lookup()
    allowed_names = location_service.get_location_names()
    history = conversation_store.get_history(session_id)
    if not history:
        return jsonify({"error": "Không tìm thấy phiên chat"}), 404
    return jsonify(
        {
            "session_id": session_id,
            "history": history,
            "detected_fields": _merge_fields_from_history(
                history, allowed_lookup=allowed_lookup, allowed_names=allowed_names
            ),
        }
    )


@chat_bp.route("/api/house/predict", methods=["POST"])
def predict_house():
    payload = request.get_json(silent=True) or {}
    location = (payload.get("location") or "").strip()
    total_sqft = payload.get("total_sqft")
    bath = payload.get("bath")
    bhk = payload.get("bhk")

    missing = []
    if not location:
        missing.append("location")
    if total_sqft is None:
        missing.append("total_sqft")
    if bath is None:
        missing.append("bath")
    if bhk is None:
        missing.append("bhk")
    if missing:
        return jsonify({"error": f"Thiếu trường: {', '.join(missing)}"}), 400

    canonical_location = location_service.canonicalize(location)
    if not canonical_location:
        return jsonify({"error": "Khu vực không hợp lệ"}), 400

    try:
        total_sqft_val = float(total_sqft)
        bath_val = int(bath)
        bhk_val = int(bhk)
    except (ValueError, TypeError):
        return jsonify({"error": "Định dạng số không hợp lệ"}), 400

    try:
        price = house_price_service.predict(
            location=canonical_location,
            total_sqft=total_sqft_val,
            bath=bath_val,
            bhk=bhk_val,
        )
    except FileNotFoundError as fnf:
        return jsonify({"error": str(fnf)}), 500
    except Exception as exc:  # pragma: no cover
        return jsonify({"error": f"Không thể dự đoán: {exc}"}), 500

    record = house_store.add_record(
        location=canonical_location,
        total_sqft=total_sqft_val,
        bath=bath_val,
        bhk=bhk_val,
        predicted_price_lakh=price,
        source="api",
    )

    return jsonify(
        {
            "input": {
                "location": canonical_location,
                "total_sqft": total_sqft_val,
                "bath": bath_val,
                "bhk": bhk_val,
            },
            "predicted_price_lakh": price,
            "record_id": record["id"],
        }
    )


@chat_bp.route("/api/locations", methods=["GET"])
def list_locations():
    locations = location_service.get_locations()
    return jsonify(
        {
            "locations": locations,
            "names": location_service.get_location_names(),
        }
    )


@chat_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})
