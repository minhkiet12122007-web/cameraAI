# views/mobile_web.py
import os
import time
from datetime import datetime
from PIL import Image
import streamlit as st
from google import genai


def show_mobile(GEMINI_API_KEY):
    # CSS Tối ưu đặc thù cho Mobile: Thu nhỏ padding màn hình, phóng to text status
    st.markdown("""
        <style>
        /* Giảm padding mặc định của Streamlit trên Mobile cho đỡ trống */
        .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        .main { background-color: #121212; color: #FFFFFF; }
        
        /* Chỉnh tiêu đề nhỏ gọn lại vừa màn hình dọc */
        h1 { color: #00E676; font-size: 24px !important; text-align: center; font-weight: bold; margin-bottom: 5px; }
        h3 { font-size: 18px !important; }
        
        .status-good { color: #00E676; font-weight: bold; font-size: 15px; text-align: center; }
        .status-warn { color: #FF1744; font-weight: bold; font-size: 15px; text-align: center; }
        .status-process { color: #FFB300; font-weight: bold; font-size: 15px; text-align: center; }
        
        /* Nút thiết kế lớn, dễ bấm bằng ngón tay */
        div.stButton > button:first-child {
            background-color: #00E676; color: black; border-radius: 12px; width: 100%; font-size: 16px; font-weight: bold; height: 55px;
        }
        /* Tối ưu khung camera gọn hơn trên màn hình đứng */
        .stCameraInput { margin-top: -10px; }
        </style>
        """, unsafe_allow_html=True)

    st.title("📱 AI FOOD SCANNER - MOBILE")
    st.write("<p style='text-align: center; font-size: 13px; color: #BBB;'>Nhấn nút bên dưới để mở Camera điện thoại</p>", unsafe_allow_html=True)

    def call_gemini_vision_api(image):
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            now = datetime.now()
            current_time_str = now.strftime("%d/%m/%Y")
            current_month = now.month

            prompt = (
                f"Bạn là một chuyên gia kiểm định thực phẩm tại Việt Nam. Hôm nay là ngày: {current_time_str}.\n"
                "Phân tích ảnh thực phẩm chụp từ camera điện thoại này và trả lời cực kỳ ngắn gọn, chủ yếu bằng gạch đầu dòng:\n\n"
                "1. 👀 ĐÁNH GIÁ CHẤT LƯỢNG: Tên, Trạng thái, và Nhãn '[THỰC PHẨM SẠCH]' hoặc '[THỰC PHẨM HỎNG]'.\n"
                f"2. 🍽️ GỢI Ý MÓN THEO MÙA: Gợi ý 2 món ăn phù hợp Tháng {current_month}.\n"
                "3. 💡 LỜI KHUYÊN: Mẹo sơ chế hoặc nấu ăn nhanh."
            )

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[image, prompt]
            )
            return response.text if response.text else "❌ Lỗi phản hồi."
        except Exception as e:
            return f"❌ Lỗi: {str(e)}"

    image_file = st.camera_input("Chụp thực phẩm")

    if image_file is not None:
        pil_image = Image.open(image_file)
        st.markdown(
            '<p class="status-process">⏳ ĐANG PHÂN TÍCH...</p>', unsafe_allow_html=True)

        with st.spinner("Đang tính toán..."):
            ai_result = call_gemini_vision_api(pil_image)

        st.markdown("### 📋 KẾT QUẢ:")
        st.info(ai_result)

        if "❌" in ai_result:
            st.markdown('<p class="status-warn">❌ LỖI HỆ THỐNG</p>',
                        unsafe_allow_html=True)
        elif any(word in ai_result.upper() for word in ["BẨN", "HỎNG", "ÔI", "THIU", "MỐC", "ĐỘC"]):
            st.markdown(
                '<p class="status-warn">⚠️ CẢNH BÁO: KHÔNG AN TOÀN!</p>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<p class="status-good">✅ THỰC PHẨM AN TOÀN</p>', unsafe_allow_html=True)
