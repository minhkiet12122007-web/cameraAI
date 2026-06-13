# -*- coding: utf-8 -*-
import os
import time
from datetime import datetime
from PIL import Image
import streamlit as st
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv
import streamlit.components.v1 as components

# Tải cấu hình bảo mật từ file .env
load_dotenv()

# Lấy API Key từ biến môi trường
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error(
        "❌ Không tìm thấy GEMINI_API_KEY. Vui lòng cấu hình trên Render hoặc file .env!")
    st.stop()

# --- CẤU HÌNH GIAO DIỆN STREAMLIT CHUNG ---
st.set_page_config(
    page_title="AI Food Scanner",
    page_icon="🥑",
    layout="centered"
)

# --- 🤖 TỰ ĐỘNG NHẬN DIỆN THIẾT BỊ BẰNG JAVASCRIPT ---
# Đoạn code này chạy ngầm để phát hiện Mobile/Desktop rồi trả kết quả về Streamlit
if "device_type" not in st.session_state:
    st.session_state.device_type = "desktop"  # Mặc định ban đầu

device_detector = """
<script>
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) 
                     || (window.innerWidth <= 768);
    const parentWindow = window.parent;
    if (isMobile) {
        parentWindow.postMessage({type: 'streamlit:setComponentValue', value: 'mobile'}, '*');
    } else {
        parentWindow.postMessage({type: 'streamlit:setComponentValue', value: 'desktop'}, '*');
    }
</script>
"""
# Chạy ngầm detector (ẩn hoàn toàn giao diện html này đi)
detected_value = components.html(device_detector, height=0, width=0)

# Cập nhật trạng thái thiết bị dựa trên màn hình người dùng
if detected_value == "mobile":
    st.session_state.device_type = "mobile"
elif detected_value == "desktop":
    st.session_state.device_type = "desktop"


# --- 🧠 HÀM GỌI API GEMINI VISION ---
def call_gemini_vision_api(image, is_mobile=False):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        now = datetime.now()
        current_time_str = now.strftime("%d/%m/%Y")
        current_month = now.month

        if is_mobile:
            # Prompt tối ưu hiển thị ngắn gọn trên màn hình điện thoại dọc
            prompt = (
                f"Bạn là một chuyên gia kiểm định thực phẩm tại Việt Nam. Hôm nay là ngày: {current_time_str}.\n"
                "Hãy nhìn vào bức ảnh thực phẩm thật kỹ và phản hồi bằng tiếng Việt ngắn gọn, chủ yếu dùng gạch đầu dòng:\n\n"
                "1. 👀 ĐÁNH GIÁ CHẤT LƯỢNG:\n"
                "   - Tên thực phẩm, trạng thái chi tiết.\n"
                "   - Ghi rõ nhãn: '[THỰC PHẨM SẠCH]' hoặc '[THỰC PHẨM HỎNG]'.\n\n"
                "2. 🍽️ GỢI Ý MÓN ĂN THEO MÙA:\n"
                f"   - Gợi ý nhanh 2 món phù hợp với thời tiết Tháng {current_month}.\n\n"
                "3. 💡 LỜI KHUYÊN:\n"
                "   - Sơ chế hoặc nấu ăn an toàn."
            )
        else:
            # Prompt đầy đủ ban đầu cho giao diện Desktop máy tính
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
                return response.text if response.text else "❌ Không nhận được phản hồi văn bản từ Gemini."
            except APIError as e:
                if e.code == 503 and attempt < max_retries - 1:
                    time.sleep(backoff_delay)
                    backoff_delay *= 2
                    continue
                return f"❌ Lỗi kết nối Google API:\n{str(e)}"
    except Exception as e:
        return f"❌ Lỗi hệ thống: {str(e)}"


# ========================================================
# XỬ LÝ RENDER GIAO DIỆN THEO THIẾT BỊ ĐÃ DETECT
# ========================================================

if st.session_state.device_type == "mobile":
    # ----------------------------------------------------
    # 📱 GIAO DIỆN TỐI ƯU TRIỆT ĐỂ CHO MOBILE
    # ----------------------------------------------------
    st.markdown("""
        <style>
        /* Ép Streamlit bỏ lề trống khổng lồ trên màn hình điện thoại */
        .block-container { 
            padding-top: 1rem !important; 
            padding-bottom: 1rem !important; 
            padding-left: 0.5rem !important; 
            padding-right: 0.5rem !important; 
            max-width: 100% !important;
        }
        .main { background-color: #121212; color: #FFFFFF; }
        
        /* Thu nhỏ chữ tiêu đề vừa khít màn hình dọc */
        h1 { color: #2979FF; font-size: 22px !important; text-align: center; font-weight: bold; margin-bottom: 5px; }
        h3 { font-size: 16px !important; margin-top: 10px; }
        .sub-text { text-align: center; font-size: 13px; color: #b0b0b0; margin-bottom: 15px; }
        
        /* Định dạng các dòng trạng thái */
        .status-good { color: #00E676; font-weight: bold; font-size: 14px; text-align: center; margin-top: 5px; }
        .status-warn { color: #FF1744; font-weight: bold; font-size: 14px; text-align: center; margin-top: 5px; }
        .status-process { color: #FFB300; font-weight: bold; font-size: 14px; text-align: center; margin-top: 5px; }
        
        /* SỬA LỖI NÚT CHỤP: CSS ép nút "Take Photo" to rộng, dễ chạm ngón tay */
        div.stButton > button:first-child {
            background-color: #2979FF !important; 
            color: white !important; 
            border-radius: 10px !important; 
            width: 100% !important; 
            font-size: 16px !important; 
            font-weight: bold !important; 
            height: 50px !important;
            border: none !important;
            box-shadow: 0px 4px 10px rgba(41, 121, 255, 0.3);
        }
        
        /* Ép khung camera input của Streamlit vừa vặn tỷ lệ màn hình dọc */
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

    st.markdown("<h1>🤖 AI FOOD SCANNER - PHIÊN BẢN MOBILE</h1>",
                unsafe_allow_html=True)
    st.markdown("<p class='sub-text'>Vui lòng cấp quyền camera, chụp ảnh thực phẩm để hệ thống tự động quét nhanh.</p>", unsafe_allow_html=True)

    st.markdown("### 📸 Camera Trực Tuyến")
    image_file = st.camera_input("Chụp ảnh thực phẩm bằng Mobile")

    if image_file is not None:
        pil_image = Image.open(image_file)
        st.markdown(
            '<p class="status-process">⏳ AI ĐANG KIỂM TRA... VUI LÒNG ĐỢI</p>', unsafe_allow_html=True)

        with st.spinner("Đang phân tích..."):
            ai_result = call_gemini_vision_api(pil_image, is_mobile=True)

        st.markdown("### 📋 KẾT QUẢ QUÊN ĐƯỢC:")
        st.info(ai_result)

        if "❌" in ai_result:
            st.markdown(
                '<p class="status-warn">❌ LỖI - VUI LÒNG THỬ LẠI</p>', unsafe_allow_html=True)
        elif any(word in ai_result.upper() for word in ["BẨN", "HỎNG", "ÔI", "THIU", "MỐC", "ĐỘC"]):
            st.markdown(
                '<p class="status-warn">⚠️ CẢNH BÁO: CÓ DẤU HIỆU THỰC PHẨM XẤU!</p>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<p class="status-good">✅ AN TOÀN - THỰC PHẨM ĐẠT TIÊU CHUẨN</p>', unsafe_allow_html=True)

else:
    # ----------------------------------------------------
    # 💻 GIAO DIỆN LAPTOP/DESKTOP (GIỮ NGUYÊN 100% BẢN ĐẸP CỦA BẠN)
    # ----------------------------------------------------
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
            ai_result = call_gemini_vision_api(pil_image, is_mobile=False)

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
