# Bengaluru House Price Prediction Chatbot

Dự án này là một ứng dụng web demo được xây dựng bằng Streamlit, cung cấp một giao diện chatbot để dự đoán giá nhà tại Bengaluru. Người dùng có thể tương tác với AI thông qua chat hoặc điền vào một biểu mẫu chi tiết để nhận được ước tính giá.

## ✨ Tính năng chính

- **Giao diện Chatbot tương tác**: Giao diện chính cho phép người dùng đặt câu hỏi bằng ngôn ngữ tự nhiên.
- **Gợi ý nhanh (Quick Prompts)**: Cung cấp các thẻ gợi ý trực quan trên màn hình chính để người dùng bắt đầu cuộc trò chuyện một cách dễ dàng.
- **Biểu mẫu nhập liệu chi tiết**: Một biểu mẫu dạng "ngăn kéo" (drawer) cho phép người dùng nhập các thông số cụ thể như diện tích, số phòng ngủ, số phòng tắm và vị trí để có dự đoán chính xác hơn.
- **Thiết kế giao diện tùy chỉnh**: Sử dụng CSS để tạo ra một giao diện hiện đại, sạch sẽ và thân thiện với người dùng, vượt ra ngoài các thành phần mặc định của Streamlit.
- **Kiến trúc mô-đun hóa**: Code được tổ chức thành các thành phần (components), logic và styles riêng biệt để dễ dàng bảo trì và mở rộng.

## 🏛️ Kiến trúc hệ thống

Hệ thống được chia thành hai phần chính: Frontend (giao diện người dùng) và Backend (logic xử lý, hiện đang được giả lập).

### 1. Frontend (`demo/frontend/`)

- **Framework**: [Streamlit](https://streamlit.io/)
- **Entry Point**: [`demo/frontend/ui.py`](demo/frontend/ui.py) là file chính để chạy ứng dụng. Nó chịu trách nhiệm:
  - Cấu hình trang và quản lý trạng thái phiên (`st.session_state`).
  - Tải các file CSS tùy chỉnh từ thư mục [`demo/frontend/styles/`](demo/frontend/styles/).
  - Điều hướng giao diện giữa trang chào mừng (landing page) và màn hình chat.
  - Hiển thị lịch sử trò chuyện và xử lý đầu vào của người dùng.
- **Components (`demo/frontend/components/`)**:
  - [`quick_prompts.py`](demo/frontend/components/quick_prompts.py): Tạo ra các thẻ gợi ý trên màn hình chính.
  - [`input_form.py`](demo/frontend/components/input_form.py): Tạo và quản lý biểu mẫu nhập liệu chi tiết.
- **Logic (`demo/frontend/logic/`)**:
  - [`api_client.py`](demo/frontend/logic/api_client.py): Chịu trách nhiệm giao tiếp với backend. **Hiện tại, file này đang giả lập (mock) các phản hồi từ bot** để phục vụ cho việc phát triển giao diện mà không cần backend thật.
- **Styling (`demo/frontend/styles/`)**:
  - Các file CSS (`main.css`, `chat_message.css`, `input_form.css`, `quick_prompts.css`) được sử dụng để tùy chỉnh giao diện của ứng dụng.

### 2. Backend (Định hướng phát triển)

- **API Endpoint**: Frontend được cấu hình để gọi đến `http://localhost:8000/chat`.
- **File chờ triển khai**: [`demo/backend/app.py`](demo/backend/app.py) là nơi dự kiến để xây dựng một API server (ví dụ: sử dụng FastAPI hoặc Flask). Server này sẽ nhận yêu cầu từ frontend, xử lý và gọi đến mô hình Machine Learning để trả về kết quả.

### 3. Machine Learning (`src/`)

- Thư mục `src` chứa các file chờ để xây dựng mô hình dự đoán giá nhà.
  - [`preprocessing.py`](src/preprocessing.py): Xử lý và làm sạch dữ liệu.
  - [`modeling.py`](src/modeling.py): Huấn luyện mô hình.
  - [`predict.py`](src/predict.py): Cung cấp hàm để thực hiện dự đoán trên dữ liệu mới.

## 🚀 Hướng dẫn chạy ứng dụng

### Yêu cầu

- Python 3.8+
- `pip`

### Các bước cài đặt và khởi chạy

1.  **Clone repository về máy của bạn.**

2.  **Tạo và kích hoạt môi trường ảo:**
    Mở terminal trong thư mục gốc của dự án và chạy các lệnh sau:

    ```bash
    # Tạo môi trường ảo
    python -m venv .myVenv

    # Kích hoạt môi trường ảo
    # Trên Windows:
    .\.myVenv\Scripts\activate
    # Trên macOS/Linux:
    # source .myVenv/bin/activate
    ```

3.  **Cài đặt các thư viện cần thiết:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Chạy ứng dụng Streamlit:**
    Đảm bảo bạn đang ở trong thư mục gốc của dự án (`Bengaluru_House`), sau đó chạy lệnh:

    ```bash
    streamlit run demo/frontend/ui.py
    ```

5.  **Mở trình duyệt và truy cập vào địa chỉ `http://localhost:8501` để xem ứng dụng.**

---
*Lưu ý: Hiện tại, tất cả các phản hồi của chatbot đều được giả lập trong file `demo/frontend/logic/api_client.py`. Để có chức năng dự đoán thật, cần phải triển khai backend và mô hình Machine Learning.*