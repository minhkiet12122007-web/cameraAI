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
    layout="wide",  # Đảm bảo layout wide để tối ưu hóa khoảng trống cho cả hai phiên bản
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
        div.stButton > button {
            background-color: #1E1E1E; color: white; border: 2px solid #2979FF; border-radius: 12px; 
            width: 100%; font-size: 18px; font-weight: bold; height: 70px; margin-bottom: 15px;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #2979FF; color: white; border-color: #2979FF; transform: scale(1.02);
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
    # KIỂU A: GIAO DIỆN MÁY TÍNH (WEB LAPTOP)
    # ----------------------------------------------------
    if st.session_state.device_layout == "desktop":
        st.markdown("""
            <style>
            .main { background-color: #121212; color: #FFFFFF; }
            h1 { color: #2979FF; font-family: 'Arial'; text-align: center; }
            .status-good { color: #00E676; font-weight: bold; font-size: 18px; text-align: center; margin-top: 10px; }
            .status-warn { color: #FF1744; font-weight: bold; font-size: 18px; text-align: center; margin-top: 10px; }
            .status-process { color: #FFB300; font-weight: bold; font-size: 18px; text-align: center; margin-top: 10px; }
            
            div.stButton > button {
                background-color: #1E1E1E !important; color: #2979FF !important; border: 1px solid #2979FF !important;
                border-radius: 8px !important; width: auto !important; padding: 5px 15px !important; height: 40px !important; font-size: 14px !important;
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
    # KIỂU B: GIAO DIỆN ĐIỆN THOẠI (ĐỒNG BỘ GIỐNG LAPTOP & CAMERA TO)
    # ----------------------------------------------------
    elif st.session_state.device_layout == "mobile":
        st.markdown("""
            <style>
            /* Ép sát lề trái phải của màn hình điện thoại */
            [data-testid="stAppViewContainer"] { padding-left: 8px !important; padding-right: 8px !important; }
            .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
            .main { background-color: #121212; color: #FFFFFF; }
            
            /* ĐỒNG BỘ TIÊU ĐỀ SANG MÀU XANH DƯƠNG GIỐNG LAPTOP */
            .mobile-title { color: #2979FF; font-size: 24px !important; text-align: center; font-weight: bold; margin-bottom: 0px; }
            
            /* ĐỒNG BỘ NÚT ĐỔI GIAO DIỆN: Giống kiểu dáng và màu sắc bên Laptop */
            div.stButton > button {
                background-color: #1E1E1E !important; color: #2979FF !important; border: 1px solid #2979FF !important;
                border-radius: 8px !important; width: auto !important; padding: 5px 15px !important; height: 38px !important; font-size: 13px !important;
                display: block; margin: 0 auto 15px auto !important; /* Căn giữa nút bấm giống Laptop */
            }
            
            /* TỐI ƯU CAMERA MOBILE TO LÊN VÀ TRÀN VIỀN */
            div[data-testid="stCameraInput"] {
                width: 100% !important;
                max-width: 100% !important;
                margin: 0px !important;
                padding: 0px !important;
            }
            /* Ép container video của camera cao lên để góc nhìn to rõ hơn */
            div[data-testid="stCameraInput"] video {
                object-fit: cover !important;
                min-height: 380px !important; /* Tăng chiều cao tối thiểu cho camera to lên */
                border-radius: 12px !important;
            }
            div[data-testid="stCameraInput"] > div {
                border: 2px solid #2979FF !important; /* Đổi viền sang màu xanh dương đồng bộ */
                border-radius: 14px !important;
            }
            
            /* Nút bấm chụp ảnh phía trong st.camera_input chuyển sang màu xanh dương */
            div[data-testid="stCameraInput"] button {
                background-color: #2979FF !important; color: white !important;
                border-radius: 8px !important; width: 100% !important;
                font-weight: bold !important; height: 45px !important; font-size: 15px !important;
            }
            
            /* Đồng bộ các thông số trạng thái báo cáo */
            .status-good { color: #00E676; font-weight: bold; font-size: 16px; text-align: center; margin-top: 10px; }
            .status-warn { color: #FF1744; font-weight: bold; font-size: 16px; text-align: center; margin-top: 10px; }
            .status-process { color: #FFB300; font-weight: bold; font-size: 16px; text-align: center; margin-top: 10px; }
            </style>
            """, unsafe_allow_html=True)

        # Nút Đổi giao diện thiết bị trên cùng, căn giữa giống hệt bản Laptop
        if st.button("🔄 Đổi giao diện thiết bị", key="mobile_switch"):
            st.session_state.device_layout = None
            st.rerun()

        st.markdown(
            "<h1 class='mobile-title'>🤖 AI FOOD SCANNER - MOBILE</h1>", unsafe_allow_html=True)
        st.write("<p style='text-align: center; font-size: 13px; color: #cccccc; margin-top:5px; margin-bottom:15px;'>Mở camera, chụp thực phẩm để quét nhanh.</p>", unsafe_allow_html=True)

        st.subheader("📸 Quét Thực Phẩm")
        # Camera đã được xử lý tăng chiều cao thông qua CSS `min-height: 380px` và màu viền xanh dương
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
