import time
# import requests # Sẽ dùng khi nối backend thật

# URL của Backend (Sẽ dùng sau này)
BACKEND_URL = "http://localhost:8000/chat" 

def get_bot_response(user_input):
    """
    Hàm gửi request sang Backend để lấy phản hồi.
    Hiện tại đang MOCK (giả lập) dữ liệu.
    """
    # --- MÔ PHỎNG GỌI API ---
    # TODO (Sau này): Thay bằng code gọi requests.post thật
    # try:
    #     response = requests.post(BACKEND_URL, json={"msg": user_input}, timeout=10)
    #     response.raise_for_status()
    #     return response.json().get("response", "Lỗi format từ server.")
    # except Exception as e:
    #     return f"Không thể kết nối đến server backend. Chi tiết: {str(e)}"

    # --- LOGIC GIẢ LẬP TẠM THỜI ---
    time.sleep(0.8) # Giả lập độ trễ mạng nhẹ
    
    input_lower = user_input.lower()
    if "giá" in input_lower:
        return "Để tôi giúp bạn định giá. Vui lòng cho biết khu vực và diện tích căn nhà?"
    elif "email" in input_lower or "viết" in input_lower:
        return "Chắc chắn rồi, tôi có thể giúp bạn soạn thảo nội dung. Bạn cần viết về chủ đề gì?"
    elif "kỹ thuật" in input_lower or "ai" in input_lower:
        return "Về mặt kỹ thuật, tôi sử dụng mô hình ngôn ngữ lớn (LLM) kết hợp với dữ liệu được huấn luyện riêng về bất động sản Bengaluru để đưa ra câu trả lời."
    else:
        return "Chào bạn! Tôi là trợ lý AI. Hãy chọn một trong các gợi ý trên màn hình hoặc nhập câu hỏi của bạn bên dưới nhé."