import streamlit as st

def show_quick_prompts():
    """
    Hiển thị 3 thẻ gợi ý nhanh.
    Trả về nội dung text nếu người dùng bấm vào một thẻ, ngược lại trả về None.
    """
    # Dữ liệu cho 3 thẻ (Icon, Tiêu đề, Nội dung chi tiết để gửi đi)
    prompts_data = [
        {
            "icon": "🏠", 
            "title": "Dự đoán giá nhà", 
            "desc": "Tại khu vực Whitefield, 2 BHK",
            "prompt_text": "Dự đoán giá nhà cho căn hộ 2 phòng ngủ (2 BHK) tại khu vực Whitefield với diện tích khoảng 1200 sqft."
        },
        {
            "icon": "📊", 
            "title": "Xu hướng giá", 
            "desc": "Phân tích các yếu tố ảnh hưởng",
            "prompt_text": "Những yếu tố nào ảnh hưởng lớn nhất đến giá nhà tại Bengaluru dựa trên dữ liệu?"
        },
        {
            "icon": "📍", 
            "title": "Khu vực đắt đỏ", 
            "desc": "Top các khu vực giá cao nhất",
            "prompt_text": "Liệt kê top 5 khu vực có giá nhà trung bình cao nhất tại Bengaluru."
        },
    ]

    st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
    
    cols = st.columns(3)
    pressed_prompt = None

    for i, col in enumerate(cols):
        data = prompts_data[i]
        with col:
            # Mẹo: Sử dụng markdown để tạo nội dung nút bấm có icon và xuống dòng
            # CSS trong main.css sẽ biến nút này thành hình thẻ card
            button_label = f"""### {data['icon']} {data['title']} \n {data['desc']}"""
            
            # Sử dụng key duy nhất cho mỗi nút để tránh lỗi Streamlit
            if st.button(button_label, key=f"prompt_btn_{i}"):
                pressed_prompt = data["prompt_text"]

    st.markdown('<div style="margin-bottom: 1rem;"></div>', unsafe_allow_html=True)
    
    return pressed_prompt