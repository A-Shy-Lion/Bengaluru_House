import streamlit as st

# SỬA DÒNG NÀY: Bỏ decorator dialog để hiển thị inline
def show_input_form(locations_list):
    """
    Hiển thị form nhập liệu và xử lý logic gửi dữ liệu.
    Args:
        locations_list (list): Danh sách các địa điểm để hiển thị trong selectbox.
    """
    # st.caption("Điền thông tin bên dưới để AI dự đoán chính xác hơn.")
    
    with st.form("house_prediction_form", border=False):
        st.markdown("#### 📝 Nhập thông số chi tiết")
        # 1. Khu vực (Selectbox)
        selected_loc = st.selectbox(
            "Khu vực (Location)", 
            options=locations_list if locations_list else ["Other"],
            index=None,
            placeholder="Gõ tên khu vực để tìm kiếm...",
            help="Gõ tên khu vực để lọc nhanh danh sách"
        )
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
             # 2. Diện tích (Number Input - Ràng buộc > 0)
            sqft = st.number_input(
                "Diện tích (sqft)", 
                min_value=300.0,    # Ràng buộc tối thiểu
                step=10.0, 
                format="%.1f",
                help="Đơn vị Square Feet. Tối thiểu 300."
            )
        with col_b:
            # 3. Số phòng ngủ (BHK - Ràng buộc số nguyên > 0)
            bhk = st.number_input(
                "Phòng ngủ (BHK)", 
                min_value=1, 
                step=1, 
                format="%d"
            )
        with col_c:
            # 4. Số phòng tắm (Ràng buộc số nguyên > 0)
            bath = st.number_input(
                "Phòng tắm", 
                min_value=1, 
                step=1, 
                format="%d"
            )
            
        # Nút submit form
        submitted = st.form_submit_button("🚀 Gửi thông tin", type="primary", use_container_width=True)
        
        if submitted:
            return {
                "location": selected_loc,
                "sqft": sqft,
                "bhk": bhk,
                "bath": bath
            }
    return None