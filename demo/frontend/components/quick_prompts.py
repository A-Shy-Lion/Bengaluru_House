import streamlit as st


def show_quick_prompts():
    """
    Hiển thị 3 thẻ gợi ý nhanh.
    Trả về nội dung text nếu người dùng bấm vào một thẻ, ngược lại trả về None.
    """
    prompts_data = [
        {
            "icon": "&#128200;",
            "title": "Dự đoán giá nhà",
            "desc": "Khu vực Whitefield, 2 BHK",
            "prompt_text": "Dự đoán giá nhà cho căn hộ 2 phòng ngủ (2 BHK) tại khu vực Whitefield với diện tích khoảng 1200 sqft.",
        },
        {
            "icon": "&#128269;",
            "title": "Xu hướng giá",
            "desc": "Phân tích yếu tố ảnh hưởng",
            "prompt_text": "Những yếu tố nào ảnh hưởng lớn nhất đến giá nhà tại Bengaluru dựa trên dữ liệu?",
        },
        {
            "icon": "&#128205;",
            "title": "Khu vực đắt đỏ",
            "desc": "Top khu vực giá cao nhất",
            "prompt_text": "Liệt kê top 5 khu vực có giá nhà trung bình cao nhất tại Bengaluru.",
        },
    ]

    cols = st.columns(3)
    # Marker để CSS bắt đúng hàng chứa prompts (phục vụ căn giữa)
    # Đặt bên trong cột đầu tiên để selector :has() hoạt động với stHorizontalBlock
    with cols[0]:
        st.markdown('<div id="quick-prompts-row-marker"></div>', unsafe_allow_html=True)

    pressed_prompt = None

    for i, col in enumerate(cols):
        data = prompts_data[i]
        with col:
            button_label = f"""### {data['icon']} {data['title']} \n {data['desc']}"""

            if st.button(button_label, key=f"prompt_btn_{i}"):
                pressed_prompt = data["prompt_text"]

    st.markdown('<div style="margin-bottom: 1rem;"></div>', unsafe_allow_html=True)

    return pressed_prompt
