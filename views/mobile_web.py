# views/mobile_web.py
import os
import streamlit as st
from PIL import Image
from datetime import datetime

# Giả sử hàm call_gemini_vision_api đã có sẵn hoặc bạn import vào đây
# Nếu bạn để hàm đó ở file khác thì hãy đảm bảo import đúng nhé.


def show_mobile(GEMINI_API_KEY, call_gemini_vision_api):
    # CSS CỰC MẠNH: Đè toàn bộ kích thước nút và camera
    st.markdown("""
        <style>
        /* 1. NÚT BẤM (SWITCH LAYOUT & NÚT CHỤP) */
        div.stButton > button {
            height: 70px !important;
            font-size: 22px !important;
            padding: 10px 20px !important;
            width: 100% !important;
            border-radius: 15px !important;
            background-color: #2979FF !important;
            color: white !important;
            font-weight: bold !important;
            border: none !important;
        }
        
        /* 2. CAMERA INPUT - PHÓNG TO CHIỀU CAO */
        div[data-testid="stCameraInput"] {
            width: 100% !important;
            min-height: 450px !important; /* Phóng to camera lên tận 450px */
            margin-bottom: 20px !important;
        }
        
        /* Làm đẹp viền camera */
        div[data-testid="stCameraInput"] > div {
            border: 3px solid #2979FF !important;
            border-radius: 20px !important;
        }
        
        /* 3. ĐIỀU CHỈNH FONT CHỮ CHO DỄ ĐỌC */
        h1, h2, h3 { color: #FFFFFF !important; }
        .stMarkdown { font-size: 18px !important; }
        
        /* Xóa khoảng cách thừa */
        .block-container { padding: 1rem !important; }
        </style>
    """, unsafe_allow_html=True)

    # Nút đổi giao diện (Đã to lên gấp 3 lần)
    if st.button("⬅️ Quay về chọn thiết bị"):
        st.session_state.device_layout = None
        st.rerun()

    st.title("📸 Camera Scan")

    # Camera giờ đã to như cái màn hình rồi
    image_file = st.camera_input("Chạm vào nút bên dưới để chụp")

    if image_file is not None:
        pil_image = Image.open(image_file)
        st.markdown(
            "<p style='text-align:center; font-size: 20px;'>⏳ Đang phân tích...</p>", unsafe_allow_html=True)

        with st.spinner("AI đang xử lý ảnh..."):
            ai_result = call_gemini_vision_api(pil_image, prompt_mode="mobile")

        st.markdown("### 📋 KẾT QUẢ:")
        st.info(ai_result)
