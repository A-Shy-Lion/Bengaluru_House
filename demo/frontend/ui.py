from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
import streamlit.components.v1 as components

# --- IMPORT CÁC MODULE ---
try:
    from logic.api_client import ApiClient, ChatResponse, DEFAULT_API_BASE
    from components.quick_prompts import show_quick_prompts
    from components.input_form import show_input_form
except ImportError as e:  # pragma: no cover - guard for bad working dir
    st.error(f"Lỗi import module: {e}. Hãy đảm bảo bạn chạy lệnh 'streamlit run' từ thư mục gốc.")
    st.stop()

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Bengaluru House Price",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- LOAD CSS ---
def load_css(file_path: Path) -> None:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Không tìm thấy file CSS: {file_path.name}")


frontend_dir = Path(__file__).parent
load_css(frontend_dir / "styles" / "main.css")
load_css(frontend_dir / "styles" / "quick_prompts.css")
load_css(frontend_dir / "styles" / "input_form.css")
load_css(frontend_dir / "styles" / "chat_message.css")

# --- SESSION STATE ---
st.session_state.setdefault("messages", [])
st.session_state.setdefault("show_form", False)
st.session_state.setdefault("session_id", "")
st.session_state.setdefault("detected_fields", {})
st.session_state.setdefault("last_prediction", None)
st.session_state.setdefault("status_text", "Sẵn sàng")
st.session_state.setdefault("history_loaded", False)
st.session_state.setdefault("api_base", os.getenv("API_BASE_URL", DEFAULT_API_BASE))

api_client = ApiClient(st.session_state.api_base)


def set_status(text: str) -> None:
    st.session_state.status_text = text


def merge_history(local: List[Dict[str, Any]], remote: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if remote:
        return remote
    return local


def sync_history_once() -> None:
    if not st.session_state.session_id or st.session_state.history_loaded:
        return
    try:
        res = api_client.fetch_history(st.session_state.session_id)
    except Exception as exc:  # pragma: no cover - runtime guard
        set_status(f"Không tải được lịch sử: {exc}")
        return
    st.session_state.messages = res.history or []
    st.session_state.detected_fields = res.detected_fields or {}
    st.session_state.last_prediction = res.prediction
    st.session_state.history_loaded = True
    set_status("Đã tải lịch sử từ backend.")


def handle_chat(user_input: str) -> None:
    """
    Gửi tin nhắn từ UI -> Backend Flask (/api/chat) -> Cập nhật lịch sử.
    """
    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("AI đang suy nghĩ..."):
        try:
            res: ChatResponse = api_client.chat(user_input, st.session_state.session_id or None)
        except Exception as exc:  # pragma: no cover - runtime guard
            st.error(f"Không gọi được API: {exc}")
            set_status(f"Lỗi API: {exc}")
            return

    st.session_state.session_id = res.session_id
    st.session_state.messages = merge_history(
        st.session_state.messages + [{"role": "assistant", "content": res.reply}],
        res.history,
    )
    st.session_state.detected_fields = res.detected_fields or {}
    st.session_state.last_prediction = res.prediction
    st.session_state.history_loaded = True
    set_status("Đã đồng bộ với backend.")


def render_detected_fields() -> None:
    fields = st.session_state.detected_fields or {}
    if not fields:
        st.caption("Chưa có trường dữ liệu dự đoán nào.")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Khu vực", fields.get("location", "-"))
        st.metric("Phòng tắm", fields.get("bath", "-"))
    with col2:
        st.metric("Diện tích (sqft)", fields.get("total_sqft", "-"))
        st.metric("Phòng ngủ (BHK)", fields.get("bhk", "-"))
    if st.session_state.last_prediction is not None:
        st.success(f"Giá dự đoán: {st.session_state.last_prediction:.2f} lakh")


# Đồng bộ lịch sử nếu đã có session id (lưu trong local state)
sync_history_once()

# Biến kiểm tra trạng thái trang
is_landing_page = len(st.session_state.messages) == 0

# --- THANH CẤU HÌNH ---
with st.sidebar:
    st.markdown("### Backend")
    api_base_input = st.text_input("API base", value=st.session_state.api_base, help="Mặc định http://localhost:5000/api")
    if api_base_input.rstrip("/") != st.session_state.api_base.rstrip("/"):
        st.session_state.api_base = api_base_input.rstrip("/")
        st.session_state.history_loaded = False
        api_client = ApiClient(st.session_state.api_base)
    st.caption(f"Session: {st.session_state.session_id or 'mới'}")
    render_detected_fields()
    if st.button("Xóa hội thoại và tạo session mới"):
        st.session_state.messages = []
        st.session_state.session_id = ""
        st.session_state.detected_fields = {}
        st.session_state.last_prediction = None
        st.session_state.history_loaded = True
        set_status("Đã tạo phiên mới.")

# --- GIAO DIỆN CHÍNH ---

# Header cố định trên đầu trang
st.markdown(
    """
    <div class="custom-header fixed-header">
        <div class="header-inner">
            <div>🏠 Bengaluru House Price</div>
            <div><img src="https://i.pinimg.com/736x/92/b2/49/92b24967cf34c2f5b82ca1ec6268fad4.jpg" width="30" style="border-radius:50%;"></div>
        </div>
    </div>
    <div style='height: 70px;'></div>
    """,
    unsafe_allow_html=True,
)

# Container chứa nội dung chat
chat_container = st.container()

# --- LOGIC ĐIỀU HƯỚNG GIAO DIỆN ---

if is_landing_page:
    with chat_container:
        st.markdown('<h1 class="welcome-title">Xin chào! <br> Bạn muốn biết thông tin gì?</h1>', unsafe_allow_html=True)
        st.markdown('<p class="welcome-subtitle">Sử dụng một trong những gợi ý phổ biến dưới đây hoặc nhập câu hỏi của bạn để bắt đầu</p>', unsafe_allow_html=True)

        user_picked_prompt = show_quick_prompts()
        if user_picked_prompt:
            handle_chat(user_picked_prompt)
            st.rerun()

else:
    with chat_container:
        st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
        for message in st.session_state.messages:
            msg_class = "st-chat-message-user" if message["role"] == "user" else "st-chat-message-assistant"
            if message["role"] == "user":
                st.markdown(
                    f"""
                <div class="st-chat-row-user">
                    <div class="{msg_class}">{message["content"]}</div>
                    <div class="st-chat-avatar-user">
                        <img src="https://i.pinimg.com/736x/92/b2/49/92b24967cf34c2f5b82ca1ec6268fad4.jpg" width="30" height="30" style="border-radius: 50%; object-fit: cover;">
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                <div class="st-chat-row-assistant">
                    <div class="st-chat-avatar-assistant">
                        <img src="https://img.freepik.com/vektoren-kostenlos/graident-ai-robot-vectorart_78370-4114.jpg" width="30" height="30" style="border-radius: 50%; object-fit: cover;">
                    </div>
                    <div class="{msg_class}">{message["content"]}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
        st.markdown('<div id="end-of-chat"></div>', unsafe_allow_html=True)

        components.html(
            """
            <script>
                const end = window.parent.document.getElementById("end-of-chat");
                if (end) {
                    end.scrollIntoView({behavior: "smooth", block: "end"});
                }
            </script>
            """,
            height=0,
            width=0,
        )


# --- THANH CHAT INPUT VỚI NÚT FORM NHỎ BÊN PHẢI ---
input_cols = st.columns([8, 1])
with input_cols[0]:
    prompt = st.chat_input("Thông tin giá nhà?... ", key="chat_input_field")
with input_cols[1]:
    st.markdown('<div id="fix-chat-button"></div>', unsafe_allow_html=True)
    btn_form = st.button("📋", help="Nhập Form", key="btn_form_small", use_container_width=True)
    if btn_form:
        st.session_state.show_form = not st.session_state.show_form
        st.rerun()

# --- FORM NHẬP LIỆU (HIỂN THỊ KHI ĐƯỢC TOGGLE) ---
if st.session_state.show_form:
    with st.container():
        st.markdown('<div id="form-anchor"></div>', unsafe_allow_html=True)

        locations_list = [
            "Electronic City",
            "Whitefield",
            "Sarjapur Road",
            "Kanakpura Road",
            "Thanisandra",
            "Yelahanka",
            "Uttarahalli",
            "Hebbal",
            "Marathahalli",
            "Raja Rajeshwari Nagar",
            "Hennur Road",
            "Bannerghatta Road",
            "7th Phase JP Nagar",
            "Haralur Road",
            "Varthur",
            "Chandapura",
            "Koramangala",
            "Kaggadasapura",
            "Bellandur",
            "Begur Road",
            "HSR Layout",
            "Kasavanhalli",
            "Electronics City Phase 1",
            "KR Puram",
            "Harlur",
            "Rajaji Nagar",
            "Hulimavu",
            "BTM Layout",
            "Ramamurthy Nagar",
            "Hosa Road",
            "Other",
        ]
        form_data = show_input_form(locations_list)

        if form_data:
            user_msg = (
                f"Dữ liệu dự đoán: location={form_data['location']}, "
                f"total_sqft={form_data['total_sqft']}, bath={form_data['bath']}, bhk={form_data['bhk']}. "
                "Hãy xử lý và tiếp tục hội thoại."
            )
            handle_chat(user_msg)
            st.session_state.show_form = False
            st.rerun()

if prompt:
    handle_chat(prompt)
    st.rerun()

# --- TRẠNG THÁI ---
st.caption(f"Trạng thái: {st.session_state.status_text}")
