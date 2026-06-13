# mobile_web.py
import streamlit as st
from PIL import Image


def show_mobile(call_gemini_vision_api):
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { padding-left: 8px !important; padding-right: 8px !important; }
        .block-container { padding-top: 0.5rem !important; padding-bottom: 1rem !important; }
        .main { background-color: #121212; color: #FFFFFF; }
        .mobile-title { color: #2979FF; font-size: 24px !important; text-align: center; font-weight: bold; margin-bottom: 0px; }
        
        /* TÙY CHỈNH NÚT ĐỔI GIAO DIỆN TRÊN MOBILE */
div.stButton {
    display: flex;
    justify-content: center;
    margin-bottom: 15px !important;
}

div.stButton > button {
    height: 55px !important;
    width: 100% !important;
    background-color: #1E1E1E !important;
    border: 2px solid #2979FF !important;
    border-radius: 10px !important;
    transition: all 0.3s ease;
}

/* Đảm bảo chữ hiển thị to rõ, đúng màu */
div.stButton > button p, div.stButton > button span {
    color: #2979FF !important;
    font-size: 16px !important;
    font-weight: bold !important;
}

/* Xóa bỏ cái khung viền focus màu xanh bị lỗi lơ lửng ở góc trái */
div.stButton > button:focus, div.stButton > button:active {
    box-shadow: none !important;
    outline: none !important;
    border-color: #2979FF !important;
}
        
        /* CAMERA TRÊN MOBILE: Bung hết chiều ngang, tăng chiều cao trục dọc */
        div[data-testid="stCameraInput"] {
            width: 100% !important;
            max-width: 100% !important;
        }
        div[data-testid="stCameraInput"] video {
            object-fit: cover !important;
            min-height: 460px !important; /* Chiều cao đứng lý tưởng cho điện thoại */
            border-radius: 14px !important;
        }
        div[data-testid="stCameraInput"] > div {
            border: 2.5px solid #2979FF !important;
            border-radius: 16px !important;
        }
        
        /* Nút chụp ảnh bên trong cụm camera mobile */
        div[data-testid="stCameraInput"] button {
            background-color: #2979FF !important; color: white !important;
            border-radius: 8px !important; width: 100% !important;
            font-weight: bold !important; height: 50px !important; font-size: 16px !important;
        }
        
        .status-good { color: #00E676; font-weight: bold; font-size: 15px; text-align: center; margin-top: 10px; }
        .status-warn { color: #FF1744; font-weight: bold; font-size: 15px; text-align: center; margin-top: 10px; }
        .status-process { color: #FFB300; font-weight: bold; font-size: 15px; text-align: center; margin-top: 10px; }
        </style>
    """, unsafe_allow_html=True)


    # 1. Hiện tiêu đề trước[cite: 1]
st.markdown("<h1 class='mobile-title'>🤖 AI FOOD SCANNER - MOBILE</h1>",
            unsafe_allow_html=True)
st.write("<p style='text-align: center; font-size: 13px; color: #cccccc; margin-top:5px; margin-bottom:15px;'>Mở camera, chụp thực phẩm để quét nhanh.</p>",
         unsafe_allow_html=True)

# 2. Hiện nút đổi giao diện ngay dưới tiêu đề[cite: 1]
if st.button("🔄 Đổi giao diện thiết bị", key="mobile_switch"):

    st.session_state.device_layout = None
    st.rerun()

    st.subheader("📸 Quét Thực Phẩm")
    image_file = st.camera_input("Chạm để chụp thực phẩm")

    if image_file is not None:
        pil_image = Image.open(image_file)
        st.markdown(
            '<p class="status-process">⏳ AI ĐANG KIỂM TRA... VUI LÒNG ĐỢI</p>', unsafe_allow_html=True)

        with st.spinner("Đang xử lý..."):
            ai_result = call_gemini_vision_api(pil_image, prompt_mode="mobile")

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
