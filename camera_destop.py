# -*- coding: utf-8 -*-
import cv2
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import pygame
import os
import time
import threading
import numpy as np
from datetime import datetime
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

# Tải cấu hình bảo mật từ file .env
load_dotenv()

# Lấy API Key an toàn từ hệ thống
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class WebcamVideoStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        if not self.stream.isOpened():
            raise RuntimeError(
                "Không thể mở camera. Vui lòng kiểm tra kết nối thiết bị hoặc chỉ số camera.")
        self.stream.set(cv2.CAP_PROP_FOURCC,
                        cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.stream.set(cv2.CAP_PROP_FPS, 60)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()


def main(root):
    if not GEMINI_API_KEY:
        print("❌ Lỗi: Không tìm thấy GEMINI_API_KEY trong file .env!")
        root.destroy()
        return

    try:
        vs = WebcamVideoStream(src=0).start()
        print("🚀 Hệ thống camera khởi động thành công.")
    except Exception as e:
        print(f"❌ Lỗi mở camera: {e}")
        root.destroy()
        return

    root.title("Hệ thống Kiểm tra Thực phẩm ")
    root.attributes('-fullscreen', True)
    root.config(bg="#121212")
    root.configure(cursor="hand2")

    def close_app(event=None):
        print("👋 Đang đóng ứng dụng...")
        vs.stop()
        pygame.mixer.quit()
        root.destroy()

    root.bind("<Escape>", close_app)
    root.bind("<q>", close_app)

    label = tk.Label(root, bg="#121212")
    label.place(x=40, y=80, width=960, height=540)

    shutter_sound = None
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        if os.path.exists("screenshot.mp3"):
            try:
                shutter_sound = pygame.mixer.Sound("screenshot.mp3")
            except Exception:
                shutter_sound = None
    except Exception:
        shutter_sound = None

    def play_shutter_sound():
        if shutter_sound:
            threading.Thread(target=shutter_sound.play, daemon=True).start()

    status_text = tk.StringVar(value="HỆ THỐNG SẴN SÀNG")
    status_label = tk.Label(root, textvariable=status_text, font=(
        "Arial", 20, "bold"), fg="#00E676", bg="#121212")
    status_label.place(x=40, y=25)

    result_frame = tk.Frame(root, bg="#1E1E1E", bd=2, relief="groove")
    result_frame.place(x=1030, y=80, width=480, height=540)

    panel_title = tk.Label(result_frame, text="KẾT QUẢ KIỂM ĐỊNH", font=(
        "Arial", 14, "bold"), fg="#FFF", bg="#2D2D2D", pady=10)
    panel_title.pack(fill="x")

    result_box = scrolledtext.ScrolledText(result_frame, font=(
        "Arial", 13), bg="#1E1E1E", fg="#FFFFFF", bd=0, wrap=tk.WORD, padx=10, pady=10)
    result_box.pack(fill="both", expand=True)
    result_box.insert(
        tk.END, "Vui lòng đưa thực phẩm trước camera và nhấn nút CHỤP để quét...")
    result_box.config(state=tk.DISABLED)

    last_frame = [None]
    captured = [False]
    analyzed_photo = [None]

    display_width = 960
    display_height = 540

    def sharpen_frame(frame):
        kernel = np.array([[-1, -1, -1], [-1,  9, -1], [-1, -1, -1]]) / 1.0
        return cv2.filter2D(frame, -1, kernel)

    def show_frame():
        if captured[0] or vs.stopped:
            return

        frame = vs.read()
        if frame is None:
            label.after(10, show_frame)
            return

        frame = cv2.flip(frame, 1)
        last_frame[0] = frame.copy()
        frame = sharpen_frame(frame)

        small_frame = cv2.resize(
            frame, (display_width, display_height), interpolation=cv2.INTER_LINEAR)
        frame_rgb = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        photo = ImageTk.PhotoImage(img)

        label.config(image=photo)
        label.image = photo
        label.after(15, show_frame)

    def call_gemini_vision_api(image_path):
        max_retries = 3
        backoff_delay = 2

        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            pil_image = Image.open(image_path)

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
                        model='gemini-2.5-flash', contents=[pil_image, prompt_text])
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
            return f"❌ Lỗi đọc ảnh hoặc khởi tạo client:\n{str(e)}"

    def capture_and_analyze(event=None):
        if captured[0] or (event and event.widget == quit_btn):
            return
        if last_frame[0] is None:
            return

        frame = last_frame[0].copy()
        status_text.set("⏳ AI ĐANG KIỂM ĐỊNH & LÊN THỰC ĐƠN THEO MÙA...")
        status_label.config(fg="#FFB300")

        result_box.config(state=tk.NORMAL)
        result_box.delete(1.0, tk.END)
        result_box.insert(
            tk.END, "\n🤖 Gemini 2.5 đang phân tích hình ảnh và tính toán thực đơn... Vui lòng đợi.")
        result_box.config(state=tk.DISABLED)

        def analyze_thread():
            temp_filename = "temp_food_capture.png"
            cv2.imwrite(temp_filename, frame)
            ai_result = call_gemini_vision_api(temp_filename)
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            root.after(0, lambda: update_ui_result(frame, ai_result))

        threading.Thread(target=analyze_thread, daemon=True).start()
        play_shutter_sound()

        flash = tk.Label(root, bg="white")
        flash.place(x=40, y=80, width=960, height=540)
        root.after(100, flash.destroy)

    def update_ui_result(captured_frame, ai_response):
        captured_rgb = cv2.cvtColor(captured_frame, cv2.COLOR_BGR2RGB)
        captured_img = Image.fromarray(captured_rgb)
        captured_img = captured_img.resize(
            (display_width, display_height), Image.LANCZOS)
        analyzed_photo[0] = ImageTk.PhotoImage(captured_img)
        label.config(image=analyzed_photo[0])
        label.image = analyzed_photo[0]

        if "❌" in ai_response:
            status_text.set("❌ LỖI KẾT NỐI API - VUI LÒNG QUÉT LẠI")
            status_label.config(fg="#FF1744")
        elif "BẨN" in ai_response.upper() or "HỎNG" in ai_response.upper() or "ÔI THIU" in ai_response.upper():
            status_text.set("⚠️ CẢNH BÁO: THỰC PHẨM CÓ DẤU HIỆU BẤT THƯỜNG!")
            status_label.config(fg="#FF1744")
        else:
            status_text.set("✅ AN TOÀN: THỰC PHẨM ĐẠT ĐỘ TƯƠI NGON")
            status_label.config(fg="#00E676")

        result_box.config(state=tk.NORMAL)
        result_box.delete(1.0, tk.END)
        result_box.insert(tk.END, ai_response)
        result_box.config(state=tk.DISABLED)

        captured[0] = True
        capture_canvas.destroy()
        retake_btn.place(relx=0.5, rely=0.92, anchor="center")

    btn_size = 120
    capture_canvas = tk.Canvas(root, width=btn_size, height=btn_size,
                               bg="#121212", highlightthickness=0, cursor="hand2")
    capture_canvas.create_oval(
        10, 10, btn_size-10, btn_size-10, fill="", outline="white", width=6)
    capture_canvas.create_oval(25, 25, btn_size-25, btn_size-25, fill="white")
    capture_canvas.place(relx=0.5, rely=0.92, anchor="center")

    capture_canvas.bind(
        "<Enter>", lambda e: capture_canvas.config(bg="#222222"))
    capture_canvas.bind(
        "<Leave>", lambda e: capture_canvas.config(bg="#121212"))
    label.bind("<Button-1>", capture_and_analyze)
    capture_canvas.bind("<Button-1>", capture_and_analyze)

    def retake():
        captured[0] = False
        retake_btn.place_forget()
        status_text.set("HỆ THỐNG SẴN SÀNG")
        status_label.config(fg="#00E676")

        result_box.config(state=tk.NORMAL)
        result_box.delete(1.0, tk.END)
        result_box.insert(
            tk.END, "Vui lòng đưa thực phẩm trước camera và nhấn nút CHỤP để quét...")
        result_box.config(state=tk.DISABLED)

        nonlocal capture_canvas
        capture_canvas = tk.Canvas(
            root, width=btn_size, height=btn_size, bg="#121212", highlightthickness=0, cursor="hand2")
        capture_canvas.create_oval(
            10, 10, btn_size-10, btn_size-10, fill="", outline="white", width=6)
        capture_canvas.create_oval(
            25, 25, btn_size-25, btn_size-25, fill="white")
        capture_canvas.place(relx=0.5, rely=0.92, anchor="center")

        capture_canvas.bind(
            "<Enter>", lambda e: capture_canvas.config(bg="#222222"))
        capture_canvas.bind(
            "<Leave>", lambda e: capture_canvas.config(bg="#121212"))
        capture_canvas.bind("<Button-1>", capture_and_analyze)
        show_frame()

    retake_btn = tk.Button(root, text="QUÉT ẢNH MỚI", font=("Arial", 16, "bold"), bg="#2979FF", fg="white",
                           padx=20, pady=10, borderwidth=0, command=retake, cursor="hand2", activebackground="#2962FF")
    retake_btn.place_forget()

    quit_btn = tk.Button(root, text="✕", font=("Arial", 20, "bold"), bg="#FF1744", fg="white",
                         borderwidth=0, command=close_app, cursor="hand2", activebackground="#D50000")
    quit_btn.place(relx=0.98, rely=0.02, anchor="ne", width=50, height=50)

    show_frame()
    root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    main(root)
