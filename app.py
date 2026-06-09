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

# Thêm CSS tùy chỉnh giao diện màu tối (Dark Mode) giống bản Desktop
st.markdown("""
    <style>
    .main { background-color: #121212; color: #FFFFFF; }
    h1 { color: #2979FF; font-family: 'Arial'; text-align: center; }
    .status-good { color: #00E676; font-weight: bold; font-size: 18px; text-align: center; }
    .status-warn { color: #FF1744; font-weight: bold; font-size: 18px; text-align: center; }
    div.stButton > button:first-child {
        background-color: #2979FF; color: white; border-radius: 8px; width: 100%; font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 AI FOOD SCANNER - PHIÊN BẢN WEB")
st.write("Vui lòng cho phép quyền truy cập camera, đưa thực phẩm trước ống kính và nhấn chụp.")

# Khung nhận hình ảnh từ Camera của thiết bị (Điện thoại/Máy tính)
img_file_buffer = st.camera_input("Quét thực phẩm")


def call_gemini_vision_api(image):
    """Gọi API Gemini Vision để phân tích chất lượng thực phẩm"""
    try:
        # Khởi tạo Client theo thư viện mới google-genai
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = (
            "Bạn là chuyên gia kiểm định an toàn thực phẩm. Hãy phân tích hình ảnh này và đưa ra kết quả ngắn gọn:\n"
            "1. Tên thực phẩm và trạng thái độ tươi ngon (Tốt/Hỏng/Cũ).\n"
            "2. Đánh giá nhanh độ an toàn vệ sinh.\n"
            "3. Gợi ý 1-2 món ăn phù hợp theo mùa dựa trên thực phẩm này.\n"
            "Lưu ý: Trả lời ngắn gọn, rõ ràng, trực tiếp bằng tiếng Việt."
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


# --- XỬ LÝ KẾT QUẢ KHI CÓ ẢNH ---
if img_file_buffer is not None:
    pil_image = Image.open(img_file_buffer)
    st.image(pil_image, caption="Ảnh thực phẩm đã chụp",
             use_container_width=True)

    with st.spinner("⏳ AI ĐANG KIỂM ĐỊNH & LÊN THỰC ĐƠN THEO MÙA..."):
        ai_result = call_gemini_vision_api(pil_image)

    # Hiển thị kết quả đánh giá lên màn hình giao diện web
    st.markdown("### 📋 KẾT QUẢ PHÂN TÍCH TỪ AI:")
    st.info(ai_result)

    # Hiển thị cảnh báo màu sắc nhanh dựa trên từ khóa kết quả
    if "❌" in ai_result:
        st.markdown(
            '<p class="status-warn">❌ LỖI HỆ THỐNG - VUI LÒNG THỬ LẠI</p>', unsafe_allow_html=True)
    elif any(word in ai_result.upper() for word in ["BẨN", "HỎNG", "ÔI", "THIU", "MỐC", "ĐỘC"]):
        st.markdown(
            '<p class="status-warn">⚠️ CẢNH BÁO: THỰC PHẨM CÓ DẤU HIỆU KHÔNG AN TOÀN!</p>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<p class="status-good">✅ THỰC PHẨM ĐẠT TIÊU CHUẨN AN TOÀN</p>', unsafe_allow_html=True)
