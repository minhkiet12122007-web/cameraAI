# desktop_web.py
import streamlit as st
from PIL import Image


def show_desktop(call_gemini_vision_api):
    st.markdown("""
        <style>
        .main { background-color: #121212; color: #FFFFFF; }
        h1 { color: #2979FF; font-family: 'Arial'; text-align: center; }
        .status-good { color: #00E676; font-weight: bold; font-size: 18px; text-align: center; margin-top: 10px; }
        .status-warn { color: #FF1744; font-weight: bold; font-size: 18px; text-align: center; margin-top: 10px; }
        .status-process { color: #FFB300; font-weight: bold; font-size: 18px; text-align: center; margin-top: 10px; }
        
        /* Giao diện nút đổi trên laptop nhỏ gọn ở góc */
        div.stButton > button {
            background-color: #1E1E1E !important; color: #2979FF !important; border: 1px solid #2979FF !important;
            border-radius: 8px !important; width: auto !important; padding: 5px 20px !important; height: 42px !important; font-size: 15px !important;
        }
        
        /* Kích thước camera vừa vặn tầm nhìn Laptop tầm 850px rộng rãi */
        div[data-testid="stCameraInput"] {
            max-width: 850px !important;
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

        # Gọi hàm được truyền từ app.py sang
        ai_result = call_gemini_vision_api(pil_image, prompt_mode="desktop")

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
