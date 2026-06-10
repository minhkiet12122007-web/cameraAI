# -*- coding: utf-8 -*-
import os
import sys
import time
from datetime import datetime
from PIL import Image
import numpy as np
import cv2
import streamlit as st
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv

# Tải cấu hình bảo mật từ file .env (Nếu chạy local)
load_dotenv()

# Lấy API Key từ biến môi trường một cách an toàn
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("❌ Không tìm thấy GEMINI_API_KEY. Vui lòng cấu hình Environment Variables trên Render hoặc kiểm tra file .env!")
    st.stop()

# --- CẤU HÌNH GIAO DIỆN STREAMLIT ---
st.set_page_config(
    page_title="Hệ thống Kiểm tra Thực phẩm AI",
    page_icon="🥑",
    layout="centered"
)

# Giao diện Dark Mode chuyên nghiệp
st.markdown("""
    <style>
    .main { background-color: #121212; color: #FFFFFF; }
    h1 { color: #2979FF; font-family: 'Arial'; text-align: center; }
    .status-good { color: #00E676; font-weight: bold; font-size: 18px; text-align: center; margin-top: 10px; }
    .status-warn { color: #FF1744; font-weight: bold; font-size: 18px; text-align: center; margin-top: 10px; }
    .status-process { color: #FFB300; font-weight: bold; font-size: 18px; text-align: center; margin-top: 10px; }
    div.stButton > button:first-child {
        background-color: #2979FF; color: white; border-radius: 8px; width: 100%; font-size: 18px; font-weight: bold; height: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 AI FOOD SCANNER - PHIÊN BẢN WEB")
st.write("Vui lòng cấp quyền truy cập camera, chụp ảnh thực phẩm và hệ thống sẽ tự động phân tích.")


def call_gemini_vision_api(image):
    """Gọi API Gemini Vision để phân tích chất lượng thực phẩm"""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        now = datetime.now()
        current_time_str = now.strftime("%d/%m/%Y")
        current_month = now.month

        prompt = (
            f"Bạn là một chuyên gia kiểm định thực phẩm kiêm đầu bếp chuyên nghiệp tại Việt Nam.\n"
            f"Hôm nay là ngày: {current_time_str} (Đang là Tháng {current_month}).\n\n"
            "Hãy nhìn vào bức ảnh thực phẩm được chụp từ camera này thật kỹ và phản hồi bằng tiếng Việt theo cấu trúc sau:\n\n"
            "1. 👀 ĐÁNH GIÁ CHẤT LƯỢNG:\n"
            "   - Tên thực phẩm là gì? Trạng thái chi tiết (tươi ngon, héo, dập, ôi thiu, có đốm nấm mốc,...).\n"
            "   - Nhãn rõ ràng: '[THỰC PHẨM SẠCH / TƯƠI NGON]' hoặc '[THỰC PHẨM CÓ DẤU HIỆU BẨN / HỎNG]'.\n\n"
            "2. 🍽️ GỢI Ý MÓN ĂN THEO MÙA (THỜI GIAN THỰC):\n"
            f"   - Dựa vào việc hiện tại đang là Tháng {current_month} tại Việt Nam, hãy gợi ý 2-3 món ăn phù hợp nhất làm từ nguyên liệu này.\n"
            "   - Ưu tiên các món ăn giải nhiệt nếu trời nóng, món ấm nóng nếu trời lạnh, hoặc các món ăn đặc trưng vùng miền vào mùa này.\n\n"
            "3. 💡 LỜI KHUYÊN NẤU NƯỚNG:\n"
            "   - Hướng dẫn sơ chế nhanh để đảm bảo an toàn hoặc mẹo nấu nguyên liệu này ngon nhất trong thời tiết hiện tại.\n\n"
            "Yêu cầu trả lời ngắn gọn, súc tích, chia các mục rõ ràng bằng markdown."
        )

        max_retries = 3
        backoff_delay = 2

        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[image, prompt]
                )
                if response.text:
                    return response.text
                return "❌ Không nhận được phản hồi văn bản từ Gemini."
            except APIError as e:
                if e.code == 503 or "demand" in str(e).lower() or "unavailable" in str(e).lower():
                    if attempt < max_retries - 1:
                        time.sleep(backoff_delay)
                        backoff_delay *= 2
                        continue
                return f"❌ Lỗi kết nối Google API:\n{str(e)}"
            except Exception as e:
                return f"❌ Lỗi hệ thống khi gọi API:\n{str(e)}"
    except Exception as e:
        return f"❌ Lỗi khởi tạo client:\n{str(e)}"


# --- KHU VỰC CAMERA CHÍNH CHỦ STREAMLIT ---
st.subheader("📸 Camera Trực Tuyến")

# st.camera_input cung cấp nút chụp chuyên nghiệp, hoạt động mượt trên cả iOS/Android
image_file = st.camera_input("Đưa thực phẩm vào khung hình bên dưới")

# --- XỬ LÝ KHI CÓ ẢNH CHỤP ---
if image_file is not None:
    # Mở ảnh bằng Pillow
    pil_image = Image.open(image_file)

    st.markdown('<p class="status-process">⏳ AI ĐANG KIỂM ĐỊNH & LÊN THỰC ĐƠN... VUI LÒNG ĐỢI</p>',
                unsafe_allow_html=True)

    with st.spinner("Đang tính toán cùng Gemini..."):
        ai_result = call_gemini_vision_api(pil_image)

    # Hiển thị kết quả
    st.markdown("### 📋 KẾT QUẢ PHÂN TÍCH TỪ AI:")
    st.info(ai_result)

    # Cảnh báo màu sắc thông minh dựa trên từ khóa kết quả
    if "❌" in ai_result:
        st.markdown(
            '<p class="status-warn">❌ LỖI HỆ THỐNG - VUI LÒNG THỬ LẠI</p>', unsafe_allow_html=True)
    elif any(word in ai_result.upper() for word in ["BẨN", "HỎNG", "ÔI", "THIU", "MỐC", "ĐỘC"]):
        st.markdown(
            '<p class="status-warn">⚠️ CẢNH BÁO: THỰC PHẨM CÓ DẤU HIỆU KHÔNG AN TOÀN!</p>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<p class="status-good">✅ THỰC PHẨM ĐẠT TIÊU CHUẨN AN TOÀN</p>', unsafe_allow_html=True)
