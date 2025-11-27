import streamlit as st


def show_input_form(locations_list):
    """
    Hiển thị form nhập liệu và trả về dict dữ liệu khi nhấn gửi.
    """
    with st.form("house_prediction_form", border=False):
        st.markdown('<div id="form-anchor"></div>', unsafe_allow_html=True)
        st.markdown("#### 🧾 Nhập thông số chi tiết")

        selected_loc = st.selectbox(
            "Khu vực (Location)",
            options=locations_list if locations_list else ["Other"],
            index=None,
            placeholder="Gõ tên khu vực để tìm nhanh...",
            help="Gõ tên khu vực để lọc nhanh danh sách",
        )

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            sqft = st.number_input(
                "Diện tích (sqft)",
                min_value=300.0,
                step=10.0,
                format="%.1f",
                help="Đơn vị Square Feet. Tối thiểu 300.",
            )
        with col_b:
            bhk = st.number_input(
                "Phòng ngủ (BHK)",
                min_value=1,
                step=1,
                format="%d",
            )
        with col_c:
            bath = st.number_input(
                "Phòng tắm",
                min_value=1,
                step=1,
                format="%d",
            )

        submitted = st.form_submit_button("📨 Gửi thông tin", type="primary", use_container_width=True)

        if submitted:
            return {
                "location": selected_loc,
                "total_sqft": sqft,
                "bhk": bhk,
                "bath": bath,
            }
    return None
