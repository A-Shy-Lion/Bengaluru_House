import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import time

# --- IMPORT CÁC MODULE ---
try:
    from logic.api_client import get_bot_response
    from components.quick_prompts import show_quick_prompts
    from components.input_form import show_input_form
except ImportError as e:
    st.error(f"Lỗi import module: {e}. Hãy đảm bảo bạn chạy lệnh 'streamlit run' từ thư mục gốc.")
    st.stop()

# --- CẤU HÌNH TRANG ---
st.set_page_config(
    page_title="Bengaluru House Price",
    page_icon="🏡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- LOAD CSS ---
def load_css(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Không tìm thấy file CSS.")


# Load main CSS
css_path = Path(__file__).parent / "styles" / "main.css"
load_css(css_path)
# Load quick prompts CSS
quick_prompts_css_path = Path(__file__).parent / "styles" / "quick_prompts.css"
load_css(quick_prompts_css_path)
# Load input form CSS
input_form_css_path = Path(__file__).parent / "styles" / "input_form.css"
load_css(input_form_css_path)
# Load chat message CSS
chat_css_path = Path(__file__).parent / "styles" / "chat_message.css"
load_css(chat_css_path)

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_form" not in st.session_state:
    st.session_state.show_form = False

# Biến kiểm tra trạng thái trang
is_landing_page = len(st.session_state.messages) == 0

# --- HÀM XỬ LÝ CHAT TRUNG TÂM (CORE LOGIC) ---
def handle_chat(user_input):
    """
    Hàm này thực hiện trọn vẹn 1 vòng: 
    User nhập -> Lưu User Msg -> Gọi Bot -> Lưu Bot Msg
    """
    # 1. Lưu tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 2. Hiển thị Spinner và Gọi Bot (Giả lập việc chờ đợi)
    # Lưu ý: Spinner này sẽ hiện ở vị trí gọi hàm
    with st.spinner("AI đang suy nghĩ..."):
        bot_reply = get_bot_response(user_input)
    
    # 3. Lưu phản hồi của Bot
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})


# ===========================
# GIAO DIỆN CHÍNH (MAIN UI)
# ===========================

# Header cố định trên đầu trang
st.markdown("""
    <div class="custom-header fixed-header">
        <div class="header-inner">
            <div>🏡 Bengaluru House Price</div>
            <div><img src="https://i.pinimg.com/736x/92/b2/49/92b24967cf34c2f5b82ca1ec6268fad4.jpg" width="30" style="border-radius:50%;"></div>
        </div>
    </div>
    <div style='height: 70px;'></div> <!-- Spacer để tránh che nội dung -->
""", unsafe_allow_html=True)

# Container chứa nội dung chat
chat_container = st.container()

# --- LOGIC ĐIỀU HƯỚNG GIAO DIỆN ---

if is_landing_page:
    with chat_container:
        # A. GIAO DIỆN LANDING PAGE
        st.markdown('<h1 class="welcome-title">Xin chào! <br> Bạn muốn biết thông tin gì?</h1>', unsafe_allow_html=True)
        st.markdown('<p class="welcome-subtitle">Sử dụng một trong những gợi ý phổ biến dưới đây hoặc nhập câu hỏi của bạn để bắt đầu</p>', unsafe_allow_html=True)
        
        # Hiển thị các nút gợi ý
        user_picked_prompt = show_quick_prompts()
        
        # ===> XỬ LÝ SỰ KIỆN CLICK NÚT TẠI ĐÂY <===
        if user_picked_prompt:
            # 1. Gọi hàm xử lý chat ngay lập tức
            handle_chat(user_picked_prompt)
            # 2. Ép trang tải lại (Rerun)
            # Khi rerun, is_landing_page sẽ thành False -> Chuyển sang giao diện Chat History
            st.rerun()

else:
    with chat_container:
        # B. GIAO DIỆN LỊCH SỬ CHAT
        st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
        for message in st.session_state.messages:
            # Chọn class CSS dựa trên vai trò
            msg_class = "st-chat-message-user" if message["role"] == "user" else "st-chat-message-assistant"
            if message["role"] == "user":
                # Avatar user bên phải, nằm ngoài box text, chỉ dùng class cho layout
                st.markdown(f'''
                <div class="st-chat-row-user">
                    <div class="{msg_class}">{message["content"]}</div>
                    <div class="st-chat-avatar-user">
                        <img src="https://i.pinimg.com/736x/92/b2/49/92b24967cf34c2f5b82ca1ec6268fad4.jpg" width="30" height="30" style="border-radius: 50%; object-fit: cover;">
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                # Avatar AI bên trái, nằm ngoài box text, dùng class cho layout
                st.markdown(f'''
                <div class="st-chat-row-assistant">
                    <div class="st-chat-avatar-assistant">
                        <img src="https://img.freepik.com/vektoren-kostenlos/graident-ai-robot-vectorart_78370-4114.jpg" width="30" height="30" style="border-radius: 50%; object-fit: cover;">
                    </div>
                    <div class="{msg_class}">{message["content"]}</div>
                </div>
                ''', unsafe_allow_html=True)

        # Spacer để đẩy nội dung lên trên footer
        st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
        # Anchor cuối cùng để đánh dấu vị trí kết thúc chat
        st.markdown('<div id="end-of-chat"></div>', unsafe_allow_html=True)

        # Tự động cuộn xuống cuối trang bằng JS
        components.html(
            """
            <script>
                // Tìm phần tử anchor
                const end = window.parent.document.getElementById("end-of-chat");
                if (end) {
                    // Cuộn phần tử vào vùng nhìn thấy
                    end.scrollIntoView({behavior: "smooth", block: "end"});
                }
            </script>
            """,
            height=0,
            width=0
        )



# --- THANH CHAT INPUT VỚI NÚT FORM NHỎ BÊN PHẢI ---
input_cols = st.columns([8, 1])
with input_cols[0]:
    prompt = st.chat_input("Thông tin giá nhà ở...", key="chat_input_field")
with input_cols[1]:
    # Anchor để CSS target đúng block này
    st.markdown('<div id="fix-chat-button"></div>', unsafe_allow_html=True)
    btn_form = st.button("📝", help="Nhập Form", key="btn_form_small", use_container_width=True)
    if btn_form:
        st.session_state.show_form = not st.session_state.show_form
        st.rerun()

# --- FORM NHẬP LIỆU (HIỂN THỊ KHI ĐƯỢC TOGGLE) ---
if st.session_state.show_form:
    with st.container():
        # Anchor để CSS target container này và biến nó thành fixed bottom drawer
        st.markdown('<div id="form-anchor"></div>', unsafe_allow_html=True)
        
        # Danh sách địa điểm phổ biến từ bộ dữ liệu Bengaluru House Price
        locations_list = [
            "Electronic City", "Whitefield", "Sarjapur Road", "Kanakpura Road", 
            "Thanisandra", "Yelahanka", "Uttarahalli", "Hebbal", "Marathahalli", 
            "Raja Rajeshwari Nagar", "Hennur Road", "Bannerghatta Road", 
            "7th Phase JP Nagar", "Haralur Road", "Varthur", "Chandapura", 
            "Koramangala", "Kaggadasapura", "Bellandur", "Begur Road", 
            "HSR Layout", "Kasavanhalli", "Electronics City Phase 1", "KR Puram", 
            "Harlur", "Rajaji Nagar", "Hulimavu", "BTM Layout", 
            "Ramamurthy Nagar", "Hosa Road", "Other"
        ]
        form_data = show_input_form(locations_list)
        
        if form_data:
            # Xử lý khi user submit form
            user_msg = f"Dự đoán giá nhà với thông tin: {form_data}"
            handle_chat(user_msg)
            st.session_state.show_form = False # Đóng form sau khi gửi
            st.rerun()

if prompt:
    handle_chat(prompt)
    st.rerun()