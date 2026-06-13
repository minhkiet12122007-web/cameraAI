# -*- coding: utf-8 -*-
import os
import sys
import time
from datetime import datetime
from PIL import Image
import streamlit as st
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv

# Import giao diện chuẩn từ 2 file bạn đã tách
# Import giao diện chuẩn từ thư mục views
from views.desktop_web import show_desktop
from views.mobile_web import show_mobile
# Tải cấu hình bảo mật từ file .env
load_dotenv()

# Lấy API Key từ biến môi trường
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error(
        "❌ Không tìm thấy GEMINI_API_KEY. Vui lòng cấu hình trên Render hoặc kiểm tra file .env!")
    st.stop()

# --- CẤU HÌNH GIAO DIỆN STREAMLIT CHUNG ---
st.set_page_config(
    page_title="Hệ thống Kiểm tra Thực phẩm AI",
    page_icon="🥑",
    layout="wide",
)

# Khởi tạo trạng thái chọn thiết bị của người dùng
if "device_layout" not in st.session_state:
    st.session_state.device_layout = None


def call_gemini_vision_api(image, prompt_mode="desktop"):
    """Hàm xử lý gọi API Gemini Vision (Được truyền sang các file giao diện)"""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        return f"❌ Lỗi khởi tạo client:\n{str(e)}"

    now = datetime.now()
    current_time_str = now.strftime("%d/%m/%Y")
    current_month = now.month

    if prompt_mode == "mobile":
        prompt = (
            f"Bạn là một chuyên gia thực phẩm Việt Nam. Hôm nay là ngày: {current_time_str}.\n"
            "Hãy nhìn ảnh thực phẩm thật kỹ và phản hồi bằng tiếng Việt cực kỳ ngắn gọn (chủ yếu gạch đầu dòng):\n\n"
            "1. 👀 ĐÁNH GIÁ CHẤT LƯỢNG:\n"
            "   - Tên thực phẩm, Trạng thái ngắn gọn.\n"
            "   - Ghi rõ nhãn: '[THỰC PHẨM SẠCH]' hoặc '[THỰC PHẨM HỎNG]'.\n\n"
            "2. 🍽️ GỢI Ý MÓN THEO MÙA:\n"
            f"   - Gợi ý nhanh 2 món ăn hợp với Tháng {current_month}.\n\n"
            "3. 💡 LỜI KHUYÊN NẤU NƯỚNG:\n"
            "   - Hướng dẫn sơ chế/mẹo nấu ăn nhanh."
        )
    else:
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
                model='gemini-2.5-flash', contents=[image, prompt])
            text = getattr(response, "text", None)
            if not text:
                try:
                    text = response.candidates[0].content
                except:
                    text = None
            if text:
                return text
            return "❌ Không nhận được phản hồi văn bản từ Gemini."
        except APIError as e:
            if getattr(e, "code", None) == 503 or "demand" in str(e).lower():
                time.sleep(backoff_delay)
                backoff_delay *= 2
                continue
            return f"❌ Lỗi kết nối Google API:\n{str(e)}"
        except Exception as e:
            return f"❌ Lỗi hệ thống khi gọi API:\n{str(e)}"


# ========================================================
# MÀN HÌNH CHỌN THIẾT BỊ BAN ĐẦU
# ========================================================
if st.session_state.device_layout is None:
    st.markdown("""
        <style>
        .main { background-color: #121212; color: #FFFFFF; }
        .welcome-title { color: #2979FF; font-family: 'Arial'; text-align: center; margin-top: 60px; font-weight: bold; }
        .welcome-sub { text-align: center; color: #aaaaaa; margin-bottom: 40px; font-size: 16px; }
        
        .stButton > button {
            background-color: #1E1E1E !important; color: white !important; border: 2px solid #2979FF !important; border-radius: 12px !important; 
            width: 100% !important; font-size: 18px !important; font-weight: bold !important; height: 70px !important; margin-bottom: 15px !important;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown("<h1 class='welcome-title'>🥑 AI FOOD SCANNER</h1>",
                unsafe_allow_html=True)
    st.markdown("<p class='welcome-sub'>Vui lòng chọn giao diện phù hợp với thiết bị của bạn:</p>",
                unsafe_allow_html=True)

    col_space1, col_content, col_space2 = st.columns([1, 2, 1])
    with col_content:
        if st.button("💻 SỬ DỤNG TRÊN MÁY TÍNH / LAPTOP", use_container_width=True):
            st.session_state.device_layout = "desktop"
            st.rerun()
        if st.button("📱 SỬ DỤNG TRÊN ĐIỆN THOẠI / MOBILE", use_container_width=True):
            st.session_state.device_layout = "mobile"
            st.rerun()

# ========================================================
# ĐIỀU HƯỚNG GIAO DIỆN VÀ TRUYỀN HÀM XỬ LÝ API
# ========================================================
else:
    if st.session_state.device_layout == "desktop":
        show_desktop(call_gemini_vision_api)
    elif st.session_state.device_layout == "mobile":
        show_mobile(call_gemini_vision_api)
