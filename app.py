# -*- coding: utf-8 -*-
import os
import time
from datetime import datetime
from PIL import Image
import streamlit as st
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv

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
    layout="centered"
)

# Khởi tạo trạng thái chọn giao diện thiết bị
if "device_layout" not in st.session_state:
    st.session_state.device_layout = None


# --- HÀM GỌI API GEMINI VISION ---
def call_gemini_vision_api(image, prompt_mode="desktop"):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        now = datetime.now()
        current_time_str = now.strftime("%d/%m/%Y")
        current_month = now.month

        if prompt_mode == "mobile":
            prompt = (
                f"Bạn là một chuyên gia thực phẩm Việt Nam. Hôm nay là ngày: {current_time_str}.\n"
                "Hãy phân tích bức ảnh thực phẩm này thật kỹ và phản hồi bằng tiếng Việt cực kỳ ngắn gọn (chủ yếu gạch đầu dòng):\n\n"
                "1. 👀 ĐÁNH GIÁ CHẤT LƯỢNG:\n"
                "   - Tên thực phẩm, Trạng thái ngắn gọn.\n"
                "   - Ghi rõ nhãn: '[THỰC PHẨM SẠCH]' hoặc '[THỰC PHẨM HỎNG]'.\n\n"
                "2. 🍽️ GỢI Ý MÓN THEO MÙA:\n"
                f"   - Gợi ý nhanh 2 món ăn hợp với Tháng {current_month}.\n\n"
                "3. 💡 LỜI KHUYÊN NẤU NƯỚNG:\n"
                "   - Mẹo sơ chế hoặc nấu ăn nhanh."
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

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image, prompt]
        )
        return response.text if response.text else "❌ Không nhận được phản hồi từ Gemini."
    except Exception as e:
        return f"❌ Lỗi hệ thống khi gọi API:\n{str(e)}"


# ========================================================
# MÀN HÌNH CHỌN THIẾT BỊ (ĐẢM BẢO KHÔNG BAO GIỜ TRẮNG TRANG)
# ========================================================
if st.session_state.device_layout is None:
    st.markdown("""
        <style>
        .main { background-color: #121212; color: #FFFFFF; }
        .welcome-title { color: #2979FF; font-family: 'Arial'; text-align: center; margin-top: 50px; font-weight: bold; }
        .welcome-sub { text-align: center; color: #aaaaaa; margin-bottom: 30px; font-size: 15px; }
        div.stButton > button {
            background-color: #1E1E1E !important; color: white !important; border: 2px solid #2979FF !important; 
            border-radius: 12px !important; width: 100% !important; font-size: 16px !important; 
            font-weight: bold !important; height: 60px !important; margin-bottom: 10px !important;
        }
        div.stButton > button:hover {
            background-color: #2979FF !important; color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown("<h1 class='welcome-title'>🥑 AI FOOD SCANNER</h1>",
                unsafe_allow_html=True)
    st.markdown("<p class='welcome-sub'>Chọn chế độ hiển thị phù hợp với thiết bị của bạn:</p>",
                unsafe_allow_html=True)

    if st.button("💻 SỬ DỤNG TRÊN MÁY TÍNH / LAPTOP", use_container_width=True):
        st.session_state.device_layout = "desktop"
        st.rerun()

    if st.button("📱 SỬ DỤNG TRÊN ĐIỆN THOẠI / MOBILE", use_container_width=True):
        st.session_state.device_layout = "mobile"
        st.rerun()

# ========================================================
# HIỂN THỊ GIAO DIỆN SAU KHI CHỌN THIẾT BỊ
# ========================================================
else:
    # Nút quay về trang lựa chọn ban đầu
    if st.button("🔄 Đổi giao diện thiết bị"):
        st.session_state.device_layout = None
        st.rerun()

    # ----------------------------------------------------
    # 💻 CẤU HÌNH GIAO DIỆN LAPTOP (GIỮ NGUYÊN BẢN ĐẸP CỦA BẠN)
    # ----------------------------------------------------
    if st.session_state.device_layout == "desktop":
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
        st.write(
            "Vui lòng cấp quyền truy cập camera, chụp ảnh thực phẩm và hệ thống sẽ tự động phân tích.")

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
    # 📱 CẤU HÌNH GIAO DIỆN MOBILE (ÉP KHUNG FIX CÁC LỖI KÌ CỤC)
    # ----------------------------------------------------
    elif st.session_state.device_layout == "mobile":
        st.markdown("""
            <style>
            /* Ép màn hình điện thoại tràn viền rộng rãi, không bị bóp lề trống */
            .block-container { 
                padding-top: 1rem !important; 
                padding-bottom: 1rem !important; 
                padding-left: 0.6rem !important; 
                padding-right: 0.6rem !important; 
                max-width: 100% !important;
            }
            .main { background-color: #121212; color: #FFFFFF; }
            
            /* Thu gọn kích thước chữ tiêu đề vừa khít màn hình đứng */
            h1 { color: #2979FF; font-size: 24px !important; text-align: center; font-weight: bold; margin-bottom: 5px; }
            h3 { font-size: 18px !important; margin-top: 15px; text-align: center; }
            .sub-desc { text-align: center; font-size: 13px; color: #b0b0b0; margin-bottom: 15px; }
            
            .status-good { color: #00E676; font-weight: bold; font-size: 15px; text-align: center; }
            .status-warn { color: #FF1744; font-weight: bold; font-size: 15px; text-align: center; }
            .status-process { color: #FFB300; font-weight: bold; font-size: 15px; text-align: center; }
            
            /* Ép nút bấm 'Chụp hình' to rõ, bo tròn vừa ngón tay chạm */
            div.stButton > button:first-child {
                background-color: #2979FF !important; 
                color: white !important; 
                border-radius: 10px !important; 
                width: 100% !important; 
                font-size: 16px !important; 
                font-weight: bold !important; 
                height: 52px !important;
                border: none !important;
            }
            
            /* FIX KHUNG CAMERA TRÊN MOBILE: Ép vừa khít chiều ngang màn hình dọc */
            [data-testid="stCameraInput"] {
                width: 100% !important;
                max-width: 100% !important;
                margin: 0 auto !important;
            }
            [data-testid="stCameraInput"] video {
                object-fit: cover !important;
                border-radius: 12px !important;
            }
            </style>
            """, unsafe_allow_html=True)

        st.title("📱 AI FOOD SCANNER")
        st.markdown(
            "<p class='sub-desc'>Chụp ảnh thực phẩm bằng camera điện thoại của bạn</p>", unsafe_allow_html=True)

        image_file = st.camera_input("Chạm để quét thực phẩm")

        if image_file is not None:
            pil_image = Image.open(image_file)
            st.markdown(
                '<p class="status-process">⏳ AI ĐANG PHÂN TÍCH... VUI LÒNG ĐỢI</p>', unsafe_allow_html=True)

            with st.spinner("Đang tính toán..."):
                ai_result = call_gemini_vision_api(
                    pil_image, prompt_mode="mobile")

            st.markdown("### 📋 KẾT QUẢ QUÉT:")
            st.info(ai_result)

            if "❌" in ai_result:
                st.markdown(
                    '<p class="status-warn">❌ LỖI HỆ THỐNG - THỬ LẠI</p>', unsafe_allow_html=True)
            elif any(word in ai_result.upper() for word in ["BẨN", "HỎNG", "ÔI", "THIU", "MỐC", "ĐỘC"]):
                st.markdown(
                    '<p class="status-warn">⚠️ CẢNH BÁO: THỰC PHẨM KHÔNG AN TOÀN!</p>', unsafe_allow_html=True)
            else:
                st.markdown(
                    '<p class="status-good">✅ AN TOÀN - THỰC PHẨM SẠCH TƯƠI</p>', unsafe_allow_html=True)
