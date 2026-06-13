# views/mobile_web.py
import os
import time
from datetime import datetime
from PIL import Image
import streamlit as st
from google import genai


def show_mobile(GEMINI_API_KEY):
    # CSS Tối ưu nâng cao dành riêng cho giao diện Điện thoại
    st.markdown("""
        <style>
        /* Tối ưu hóa nền và khoảng cách toàn màn hình */
        .block-container { 
            padding-top: 0.5rem !important; 
            padding-bottom: 1rem !important; 
            padding-left: 0.8rem !important; 
            padding-right: 0.8rem !important; 
        }
        .main { background-color: #121212; color: #FFFFFF; }
        
        /* Định dạng tiêu đề Mobile */
        .mobile-title {
            color: #00E676; 
            font-size: 26px !important; 
            text-align: center; 
            font-weight: bold; 
            margin-bottom: 2px;
            text-shadow: 0px 2px 4px rgba(0,0,0,0.5);
        }
        .mobile-subtitle {
            text-align: center; 
            font-size: 13px; 
            color: #aaaaaa; 
            margin-bottom: 15px;
        }
        
        /* 🔥 BÍ QUYẾT ÉP CAMERA FULL-WIDTH & ĐẸP TRÊN ĐIỆN THOẠI */
        div[data-testid="stCameraInput"] {
            width: 100% !important;
            max-width: 100% !important;
            padding: 0px !important;
            border-radius: 16px !important;
            overflow: hidden !important;
            box-shadow: 0 4px 15px rgba(0, 230, 118, 0.2);
        }
        
        /* Ẩn bớt các chỉ dẫn rườm rà của nút mặc định trong st.camera_input để đỡ chật */
        div[data-testid="stCameraInput"] button {
            background-color: #00E676 !important;
            color: black !important;
            font-weight: bold !important;
            border-radius: 8px !important;
        }
        
        /* Trạng thái thông báo */
        .status-process { color: #FFB300; font-weight: bold; font-size: 16px; text-align: center; margin: 15px 0; }
        .status-warn { color: #FF1744; font-weight: bold; font-size: 16px; text-align: center; margin: 15px 0; }
        
        /* Làm đẹp hộp kết quả */
        div.stAlert {
            background-color: #1E1E1E !important;
            border-left: 5px solid #00E676 !important;
            color: #FFFFFF !important;
            border-radius: 12px !important;
        }
        </style>
        """, unsafe_allow_html=True)

    # Hiển thị tiêu đề dạng Custom HTML để ăn theo CSS Mobile tốt hơn
    st.markdown('<p class="mobile-title">📱 AI FOOD SCANNER</p>',
                unsafe_allow_html=True)
    st.markdown('<p class="mobile-subtitle">Chạm nút bên dưới để mở camera hoặc chụp quét</p>',
                unsafe_allow_html=True)

    def call_gemini_vision_api(image):
        try:
            # Khởi tạo client với API key chuẩn của thư viện google-genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            current_month = datetime.now().month

            prompt = (
                "Bạn là một chuyên gia kiểm định thực phẩm thông minh. Hãy nhìn vào hình ảnh và phản hồi theo các mục sau bằng tiếng Việt rõ ràng:\n"
                "1. 🥑 ĐÁNH GIÁ CHẤT LƯỢNG: Tên thực phẩm, Trạng thái (Tươi ngon/Hỏng/Cần chú ý), kèm nhãn '[THỰC PHẨM SẠCH]' hoặc '[THỰC PHẨM HỎNG]'.\n"
                f"2. 🍽️ GỢI Ý MÓN THEO MÙA: Gợi ý đúng 2 món ăn phù hợp thời tiết Tháng {current_month}.\n"
                "3. 💡 LỜI KHUYÊN: Mẹo sơ chế bảo quản nhanh gọn."
            )

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[image, prompt]
            )
            return response.text if response.text else "❌ Lỗi: Không nhận được phản hồi từ AI."
        except Exception as e:
            return f"❌ Lỗi hệ thống: {str(e)}"

    # Thành phần camera đã được ép CSS tràn chiều ngang
    image_file = st.camera_input("Bấm để chụp ảnh thực phẩm")

    if image_file is not None:
        pil_image = Image.open(image_file)
        st.markdown(
            '<p class="status-process">⏳ AI ĐANG KIỂM TRA... VUI LÒNG ĐỢI</p>', unsafe_allow_html=True)

        with st.spinner("Đang phân tích..."):
            ai_result = call_gemini_vision_api(pil_image)

        st.markdown("### 📋 KẾT QUẢ QUÉT ĐƯỢC:")
        st.info(ai_result)

        if "❌" in ai_result:
            st.markdown(
                '<p class="status-warn">❌ CÓ LỖI XẢY RA - VUI LÒNG THỬ LẠI</p>', unsafe_allow_html=True)
