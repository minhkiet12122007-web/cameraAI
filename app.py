# -*- coding: utf-8 -*-
from google.genai.errors import APIError
from google import genai
from datetime import datetime
import time
from PIL import Image
import numpy as np
import cv2
import streamlit as st
import sys
import os
from dotenv import load_model, load_dotenv

# Tải cấu hình bảo mật từ file .env
load_dotenv()

# Detect common debugger launchers (debugpy) or IDE debug envs and exit
_argv_join = " ".join(sys.argv).lower()
if "debugpy" in _argv_join or os.environ.get("PYCHARM_HOSTED") or os.environ.get("VSCODE_PID"):
    print("Detected debugger environment. To run the Streamlit app, use:\n\n    streamlit run app.py\n")
    sys.exit(0)

# Lấy API Key từ biến môi trường một cách an toàn
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("❌ Không tìm thấy GEMINI_API_KEY. Vui lòng kiểm tra lại file .env!")
    st.stop()

if any("debugpy" in str(s).lower() for s in sys.argv):
    print("Detected debugger environment. Please run this app with:\n\n    streamlit run app.py\n")
    sys.exit(0)

st.set_page_config(
    page_title="Hệ thống Kiểm tra Thực phẩm AI",
    page_icon="🤖",
    layout="centered"
)

st.markdown("""
    <style>
    .main { background-color: #121212; color: #FFFFFF; }
    div.stButton > button:first-child {
        background-color: #2979FF; color: white; border-radius: 8px; font-weight: bold;
    }
    .status-good { color: #00E676; font-weight: bold; font-size: 20px; }
    .status-warn { color: #FF1744; font-weight: bold; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 Hệ Thống Kiểm Định Thực Phẩm")
st.write("Vui lòng đưa thực phẩm trước camera điện thoại và nhấn nút chụp...")

img_file_buffer = st.camera_input("Chụp ảnh thực phẩm")


def call_gemini_vision_api(pil_image):
    max_retries = 3
    backoff_delay = 2

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        now = datetime.now()
        current_time_str = now.strftime("%d/%m/%Y")
        current_month = now.month

        prompt_text = (
            f"Bạn là một chuyên gia kiểm định thực phẩm kiêm đầu bếp chuyên nghiệp tại Việt Nam.\n"
            f"Hôm nay là ngày: {current_time_str} (Đang là Tháng {current_month}).\n\n"
            "Hãy nhìn vào bức ảnh thực phẩm được chụp từ camera này thật kỹ và phản hồi bằng tiếng Việt theo cấu trúc sau:\n\n"
            "1. 👀 ĐÁNH GIÁ CHẤT LƯỢNG:\n"
            "   - Tên thực phẩm là gì? Trạng thái chi tiết (tươi ngon, héo, dập, ôi thiu, có đốm nấm mốc,...).\n"
            "   - Nhãn rõ ràng: '[THỰC PHẨM SẠCH / TƯƠI NGON]' hoặc '[THỰC PHẨM CÓ DẤU HIỆU BẨN / HỎNG]'.\n\n"
            "2. 🍽️ GỢI Ý MÓN ĂN THEO MÙA (THỜI GIAN THỰC):\n"
            f"   - Dựa vào việc hiện tại đang là Tháng {current_month} tại Việt Nam (hãy tự xác định đặc trưng thời tiết lúc này là mùa hè oi bức, mùa đông lạnh, hay mùa mưa...), hãy gợi ý 2-3 món ăn phù hợp nhất làm từ nguyên liệu này.\n"
            "   - Ưu tiên các món ăn giải nhiệt nếu trời nóng, món ấm nóng nếu trời lạnh, hoặc các món ăn đặc trưng vùng miền vào mùa này.\n\n"
            "3. 💡 LỜI KHUYÊN NẤU NƯỚNG:\n"
            "   - Hướng dẫn sơ chế nhanh để đảm bảo an toàn hoặc mẹo nấu nguyên liệu này ngon nhất trong thời tiết hiện tại.\n\n"
            "Yêu cầu trả lời ngắn gọn, súc tích, chia các mục rõ ràng bằng markdown."
        )

        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[pil_image, prompt_text]
                )
                if response.text:
                    return response.text
                else:
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


if img_file_buffer is not None:
    pil_image = Image.open(img_file_buffer)
    st.image(pil_image, caption="Ảnh thực phẩm đã chụp",
             use_container_width=True)

    with st.spinner("⏳ AI ĐANG KIỂM ĐỊNH & LÊN THỰC ĐƠN THEO MÙA..."):
        ai_result = call_gemini_vision_api(pil_image)

    if "❌" in ai_result:
        st.markdown(
            '<p class="status-warn">❌ LỖI KẾT NỐI API - VUI LÒNG QUÉT LẠI</p>', unsafe_allow_html=True)
    elif any(word in ai_result.upper() for word in ["BẨN", "HỎNG", "ÔI THIU"]):
        st.markdown(
            '<p class="status-warn">⚠️ CẢNH BÁO: THỰC PHẨM CÓ DẤU HIỆU BẤT THƯỜNG!</p>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<p class="status-good">✅ AN TOÀN: THỰC PHẨM ĐẠT ĐỘ TƯƠI NGON</p>', unsafe_allow_html=True)

    st.subheader("KẾT QUẢ KIỂM ĐỊNH")
    st.markdown(ai_result)
