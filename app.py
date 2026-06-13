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

# --- CẤU HÌNH GIAO DIỆN STREAMLIT CHUNG ---
st.set_page_config(
    page_title="Hệ thống Kiểm tra Thực phẩm AI",
    page_icon="🥑",
    layout="wide",  # Đảm bảo layout wide để kiểm soát CSS tốt hơn
)

# Khởi tạo trạng thái chọn thiết bị của người dùng (nếu chưa có trong session)
if "device_layout" not in st.session_state:
    st.session_state.device_layout = None


def call_gemini_vision_api(image, prompt_mode="desktop"):
    """Gọi API Gemini Vision để phân tích chất lượng thực phẩm."""
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
                except Exception:
                    text = None
            if text:
                return text
            return "❌ Không nhận được phản hồi văn bản từ Gemini."
        except APIError as e:
            if getattr(e, "code", None) == 503 or "demand" in str(e).lower() or "unavailable" in str(e).lower():
                if attempt < max_retries - 1:
                    time.sleep(backoff_delay)
                    backoff_delay *= 2
                    continue
            return f"❌ Lỗi kết nối Google API:\n{str(e)}"
        except Exception as e:
            return f"❌ Lỗi hệ thống khi gọi API:\n{str(e)}"


# ========================================================
# MÀN HÌNH ĐIỀU HƯỚNG CHỌN GIAO DIỆN (BAN ĐẦU)
# ========================================================
if st.session_state.device_layout is None:
    st.markdown("""
        <style>
        .main { background-color: #121212; color: #FFFFFF; }
        .welcome-title { color: #2979FF; font-family: 'Arial'; text-align: center; margin-top: 60px; font-weight: bold; }
        .welcome-sub { text-align: center; color: #aaaaaa; margin-bottom: 40px; font-size: 16px; }
        
        /* CSS cho 2 nút chọn thiết bị ban đầu to rõ, đẹp mắt */
        .stButton > button {
            background-color: #1E1E1E !important; color: white !important; border: 2px solid #2979FF !important; border-radius: 12px !important; 
            width: 100% !important; font-size: 18px !important; font-weight: bold !important; height: 70px !important; margin-bottom: 15px !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            background-color: #2979FF !important; color: white !important; border-color: #2979FF !important; transform: scale(1.02) !important;
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
# SAU KHI ĐÃ CHỌN GIAO DIỆN THIẾT BỊ
# ========================================================
else:
    # ----------------------------------------------------
    # KIỂU A: GIAO DIỆN MÁY TÍNH (WEB LAPTOP) - CAMERA NHỎ LẠI
    # ----------------------------------------------------
    if st.session_state.device_layout == "desktop":
        st.markdown("""
            <style>
            .main { background-color: #121212; color: #FFFFFF; }
            h1 { color: #2979FF; font-family: 'Arial'; text-align: center; }
            .status-good { color: #00E676; font-weight: bold; font-size: 18px; text-align: center; margin-top: 10px; }
            .status-warn { color: #FF1744; font-weight: bold; font-size: 18px; text-align: center; margin-top: 10px; }
            .status-process { color: #FFB300; font-weight: bold; font-size: 18px; text-align: center; margin-top: 10px; }
            
            /* Nút đổi giao diện trên bản Desktop nhỏ gọn vừa phải ở góc */
            .stButton > button {
                background-color: #1E1E1E !important; color: #2979FF !important; border: 1px solid #2979FF !important;
                border-radius: 8px !important; width: auto !important; padding: 5px 20px !important; height: 42px !important; font-size: 15px !important;
            }
            
            /* THU NHỎ CAMERA BÊN LAPTOP: Giới hạn độ rộng tối đa và căn giữa */
            div[data-testid="stCameraInput"] {
                max-width: 550px !important;
                margin: 0 auto !important;
            }
            div[data-testid="stCameraInput"] button {
                background-color: #2979FF !important; color: white !important; border-radius: 8px !important;
            }
            </style>
            """, unsafe_allow_html=True)

        if st.button("🔄 Đổi giao diện thiết bị", key="desktop_switch"):
            st.session_state.device_layout = None
            st.rerun()

        st.title("🤖 AI FOOD SCANNER - PHIÊN BẢN WEB")
        st.write("<p style='text-align: center;'>Vui lòng cấp quyền truy cập camera, chụp ảnh thực phẩm và hệ thống sẽ tự động phân tích.</p>", unsafe_allow_html=True)

        st.subheader("📸 Camera Trực Tuyến")
        image_file = st.camera_input("Đưa thực phẩm vào khung hình bên dưới")

        if image_file is not None:
            pil_image = Image.open(image_file)
            st.markdown(
                '<p class="status-process">⏳ AI ĐANG KIỂM ĐỊNH & LÊN THỰC ĐƠN... VUI LÒNG ĐỢI</p>', unsafe_allow_html=True)

            with st.spinner("Đang tính toán cùng Gemini..."):
                ai_result = call_gemini_vision_api(
                    pil_image, prompt_mode="desktop")

            st.markdown("### 📋 KẾT QUẢ PHÂN TÍCH TỪ AI:")
            st.info(ai_result)

            if "❌" in ai_result:
                st.markdown(
                    '<p class="status-warn">❌ LỖI HỆ THỐNG - VUI LÒNG THỬ LẠI</p>', unsafe_allow_html=True)
            elif any(word in ai_result.upper() for word in ["BẨN", "HỎNG", "ÔI", "THIU", "MỐC", "ĐỘC"]):
                st.markdown(
                    '<p class="status-warn">⚠️ CẢNH BÁO: THỰC PHẨM CÓ DẤU HIỆU KHÔNG AN TOÀN!</p>', unsafe_allow_html=True)
            else:
                st.markdown(
                    '<p class="status-good">✅ THỰC PHẨM ĐẠT TIÊU CHUẨN AN TOÀN</p>', unsafe_allow_html=True)

    # ----------------------------------------------------
    # KIỂU B: GIAO DIỆN ĐIỆN THOẠI - NÚT TO RÕ CHỮ, CAMERA PHÓNG TO
    # ----------------------------------------------------
    elif st.session_state.device_layout == "mobile":
        st.markdown("""
            <style>
            [data-testid="stAppViewContainer"] { padding-left: 10px !important; padding-right: 10px !important; }
            .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
            .main { background-color: #121212; color: #FFFFFF; }
            
            .mobile-title { color: #2979FF; font-size: 24px !important; text-align: center; font-weight: bold; margin-bottom: 0px; }
            
            /* SỬA NÚT ĐỔI GIAO DIỆN TRÊN MOBILE: Ép kích thước to lớn, rõ chữ, căn giữa màn hình */
            .mobile-switch-box {
                width: 100% !important;
                text-align: center !important;
                margin-bottom: 15px !important;
            }
            .mobile-switch-box button {
                height: 55px !important;
                width: 85% !important;
                font-size: 17px !important;
                font-weight: bold !important;
                color: #2979FF !important;
                background-color: #1E1E1E !important;
                border: 2px solid #2979FF !important;
                border-radius: 10px !important;
                display: block !important;
                margin: 0 auto !important;
            }
            
            /* PHÓNG TO CAMERA TRÊN MOBILE */
            div[data-testid="stCameraInput"] {
                width: 100% !important;
                max-width: 100% !important;
                margin: 0px !important;
                padding: 0px !important;
            }
            /* Ép luồng phát video của camera kéo dài trục dọc */
            div[data-testid="stCameraInput"] video {
                object-fit: cover !important;
                min-height: 440px !important;   /* Tăng hẳn chiều cao camera lên 440px để nhìn cực to */
                border-radius: 14px !important;
            }
            div[data-testid="stCameraInput"] > div {
                border: 2.5px solid #2979FF !important;
                border-radius: 16px !important;
            }
            
            /* Nút chụp bên trong cụm camera trên Mobile */
            div[data-testid="stCameraInput"] button {
                background-color: #2979FF !important; color: white !important;
                border-radius: 8px !important; width: 100% !important;
                font-weight: bold !important; height: 48px !important; font-size: 16px !important;
            }
            
            .status-good { color: #00E676; font-weight: bold; font-size: 16px; text-align: center; margin-top: 10px; }
            .status-warn { color: #FF1744; font-weight: bold; font-size: 16px; text-align: center; margin-top: 10px; }
            .status-process { color: #FFB300; font-weight: bold; font-size: 16px; text-align: center; margin-top: 10px; }
            </style>
            """, unsafe_allow_html=True)

        # Đặt nút đổi giao diện vào một container custom riêng để ăn theo CSS độc lập
        st.markdown('<div class="mobile-switch-box">', unsafe_allow_html=True)
        if st.button("🔄 Đổi giao diện thiết bị", key="mobile_switch"):
            st.session_state.device_layout = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            "<h1 class='mobile-title'>🤖 AI FOOD SCANNER - MOBILE</h1>", unsafe_allow_html=True)
        st.write("<p style='text-align: center; font-size: 14px; color: #cccccc; margin-top:5px; margin-bottom:15px;'>Mở camera, chụp thực phẩm để quét nhanh.</p>", unsafe_allow_html=True)

        st.subheader("📸 Quét Thực Phẩm")
        image_file = st.camera_input("Chạm để chụp thực phẩm")

        if image_file is not None:
            pil_image = Image.open(image_file)
            st.markdown(
                '<p class="status-process">⏳ AI ĐANG KIỂM TRA... VUI LÒNG ĐỢI</p>', unsafe_allow_html=True)

            with st.spinner("Đang xử lý..."):
                ai_result = call_gemini_vision_api(
                    pil_image, prompt_mode="mobile")

            st.markdown("### 📋 KẾT QUẢ QUÉT ĐƯỢC:")
            st.info(ai_result)

            if "❌" in ai_result:
                st.markdown(
                    '<p class="status-warn">❌ LỖI - VUI LÒNG THỬ LẠI</p>', unsafe_allow_html=True)
            elif any(word in ai_result.upper() for word in ["BẨN", "HỎNG", "ÔI", "THIU", "MỐC", "ĐỘC"]):
                st.markdown(
                    '<p class="status-warn">⚠️ CẢNH BÁO: CÓ DẤU HIỆU XẤU / HỎNG!</p>', unsafe_allow_html=True)
            else:
                st.markdown(
                    '<p class="status-good">✅ AN TOÀN - THỰC PHẨM TƯƠI SẠCH</p>', unsafe_allow_html=True)
