import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import pyttsx3
import time
import threading
import pyautogui
import os
import sys
import urllib.request
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Configuration ---
MODEL_PATH = resource_path('face_landmarker.task')
EAR_THRESHOLD = 0.20
CLICK_COOLDOWN = 1.0
MIN_ALPHA = 0.05
MAX_ALPHA = 0.25
SENSITIVITY_X = 1.0
SENSITIVITY_Y = 1.0

PHRASES = ["I need help", "Yes", "No", "Thank you", "Water please", "Food please", "Toilet"]

# --- Automatic Model Download helper ---
def check_and_download_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading face_landmarker.task model. Please wait...")
        url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
        try:
            urllib.request.urlretrieve(url, MODEL_PATH)
            print("Download completed successfully!")
        except Exception as e:
            print(f"Error downloading model: {e}")
            sys.exit(1)

class Dashboard:
    def __init__(self, root, start_callback):
        self.root = root
        self.root.title("Neuro Dristi Dashboard")
        self.root.geometry("600x500")
        self.root.configure(bg="#1e1e1e")
        self.root.resizable(False, False)
        
        # Load and set Icon
        try:
            self.root.iconbitmap(resource_path("app_icon.ico"))
        except:
            pass

        # Main Layout
        self.main_frame = tk.Frame(root, bg="#1e1e1e")
        self.main_frame.pack(expand=True, fill="both")

        # Logo/Title
        self.title_label = tk.Label(self.main_frame, text="NEURO DRISTI", 
                                    font=("Helvetica", 32, "bold"), fg="#00b4ff", bg="#1e1e1e")
        self.title_label.pack(pady=(50, 10))

        self.subtitle_label = tk.Label(self.main_frame, text="Eye-Controlled Speech Systems", 
                                       font=("Helvetica", 14), fg="#888888", bg="#1e1e1e")
        self.subtitle_label.pack(pady=(0, 40))

        # Start Button
        self.start_btn = tk.Button(self.main_frame, text="START SYSTEM", 
                                   command=start_callback,
                                   font=("Helvetica", 16, "bold"),
                                   bg="#00b4ff", fg="white",
                                   activebackground="#0088cc", activeforeground="white",
                                   relief="flat", cursor="hand2", padx=40, pady=15)
        self.start_btn.pack(pady=20)

        # Footer Info
        self.info_label = tk.Label(self.main_frame, 
                                   text="Controls: Head Movement = Mouse | Blink/Wink = Click\nPress ESC in the app to quit", 
                                   font=("Helvetica", 10), fg="#666666", bg="#1e1e1e")
        self.info_label.pack(side="bottom", pady=20)

class NeuroDristi:
    def __init__(self):
        # MediaPipe Setup (No windows yet)
        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            num_faces=1)
        self.detector = vision.FaceLandmarker.create_from_options(options)
        
        # State
        self.tts_busy = False
        self.keyboard_text = ""
        
        # Tracking
        self.screen_w, self.screen_h = pyautogui.size()
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
        
        self.last_x, self.last_y = None, None
        self.range_x = [0.38, 0.62]
        self.range_y = [0.38, 0.62]
        self.last_click_time = 0
        
        # UI Windows Configuration
        self.win_ctrl = "Neuro Dristi Control"
        self.win_kb = "Neuro Dristi Keyboard"
        self.kw_w, self.kw_h = 720, 500
        
        # Keyboard Grid
        self.kb_rows = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'BS'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '.', ',', 'CLR'],
            ['SPACE', 'ENTER', 'EXIT']
        ]

    def speak(self, text):
        if not self.tts_busy and text.strip():
            self.tts_busy = True
            def _speak_thread():
                try:
                    engine = pyttsx3.init()
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()
                except Exception as e:
                    print(f"TTS Error: {e}")
                finally:
                    self.tts_busy = False
            threading.Thread(target=_speak_thread, daemon=True).start()

    def get_ear(self, landmarks):
        p2, p6, p1, p4 = landmarks[159], landmarks[145], landmarks[33], landmarks[133]
        dist_v = np.sqrt((p2.x - p6.x)**2 + (p2.y - p6.y)**2)
        dist_h = np.sqrt((p1.x - p4.x)**2 + (p1.y - p4.y)**2)
        return dist_v / dist_h if dist_h != 0 else 0

    def dynamic_smoothing(self, target, last):
        if last is None: return target
        dist = np.abs(target - last)
        alpha = np.clip(dist * 2.0, MIN_ALPHA, MAX_ALPHA)
        return last + alpha * (target - last)

    def draw_glass_panel(self, img, w, h, title="", color=(30, 30, 30)):
        img[:] = color
        cv2.rectangle(img, (0, 0), (w-2, h-2), (100, 100, 100), 2)
        if title:
            cv2.putText(img, title, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 180, 255), 2)

    def draw_button(self, img, x, y, w, h, text, is_hovered, color=(55, 55, 55)):
        bg_col = (0, 140, 255) if is_hovered else color
        brd_col = (255, 255, 255) if is_hovered else (180, 180, 180)
        cv2.rectangle(img, (x, y), (x + w, y + h), bg_col, -1)
        cv2.rectangle(img, (x, y), (x + w, y + h), brd_col, 2)
        
        font_scale = 0.7
        for _ in range(5):
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
            if tw < w - 15 or font_scale < 0.4: break
            font_scale -= 0.1
            
        cv2.putText(img, text, (x + (w - tw) // 2, y + (h + th) // 2), 
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 2)

    def run_tracking(self):
        cv2.namedWindow(self.win_ctrl, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.win_ctrl, 420, 920)
        cv2.moveWindow(self.win_ctrl, 20, 30)
        
        self.kw_w, self.kw_h = 720, 500
        cv2.namedWindow(self.win_kb, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.win_kb, self.kw_w, self.kw_h)
        cv2.moveWindow(self.win_kb, self.screen_w - self.kw_w - 20, self.screen_h - self.kw_h - 75)
        
        try:
            cv2.setWindowProperty(self.win_ctrl, cv2.WND_PROP_TOPMOST, 1)
            cv2.setWindowProperty(self.win_kb, cv2.WND_PROP_TOPMOST, 1)
        except:
            pass

        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            success, frame = cap.read()
            if not success: break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            detection_result = self.detector.detect(mp_image)

            mx, my = pyautogui.position()
            trigger_click = False

            if detection_result.face_landmarks:
                landmarks = detection_result.face_landmarks[0]
                nose = landmarks[1]
                tx = np.interp(nose.x, (self.range_x[0], self.range_x[1]), (0, self.screen_w))
                ty = np.interp(nose.y, (self.range_y[0], self.range_y[1]), (0, self.screen_h))
                self.last_x, self.last_y = self.dynamic_smoothing(tx, self.last_x), self.dynamic_smoothing(ty, self.last_y)
                pyautogui.moveTo(int(np.clip(self.last_x, 0, self.screen_w - 1)), 
                                 int(np.clip(self.last_y, 0, self.screen_h - 1)), _pause=False)
                
                if self.get_ear(landmarks) < EAR_THRESHOLD and (time.time() - self.last_click_time) > CLICK_COOLDOWN:
                    self.last_click_time, trigger_click = time.time(), True
                    pyautogui.click()

            # --- WINDOW 1: CONTROL ---
            cw, ch = 420, 850
            f_ctrl = np.zeros((ch, cw, 3), dtype=np.uint8)
            self.draw_glass_panel(f_ctrl, cw, ch, "NEURO DRISTI - QUICK PHRASES")
            cam_feed = cv2.resize(frame, (380, 285))
            f_ctrl[60:60+285, 20:20+380] = cam_feed
            
            try:
                wx1, wy1, ww1, wh1 = cv2.getWindowImageRect(self.win_ctrl)
                rx1, ry1 = mx - wx1, my - wy1
            except:
                wx1 = int(cv2.getWindowProperty(self.win_ctrl, cv2.WND_PROP_X))
                wy1 = int(cv2.getWindowProperty(self.win_ctrl, cv2.WND_PROP_Y))
                rx1, ry1 = mx - wx1, my - (wy1 + 32)

            cb_x, cb_y, cb_w, cb_h = 10, 350, 400, 60
            is_close_h = (cb_x < rx1 < cb_x + cb_w) and (cb_y < ry1 < cb_y + cb_h)
            self.draw_button(f_ctrl, cb_x, cb_y, cb_w, cb_h, "EXIT APPLICATION", is_close_h, (30, 30, 100))
            if is_close_h and trigger_click: os._exit(0)

            for i, p in enumerate(PHRASES):
                bx, by, bw, bh = 10, 420 + (i * 70), 400, 65
                is_h = (bx < rx1 < bx + bw) and (by < ry1 < by + bh)
                if is_h and trigger_click: self.speak(p)
                self.draw_button(f_ctrl, bx, by, bw, bh, p, is_h, (40, 40, 60))
            
            if 0 < rx1 < cw and 0 < ry1 < ch:
                cv2.circle(f_ctrl, (rx1, ry1), 4, (0, 180, 255), -1)

            # --- WINDOW 2: KEYBOARD ---
            kw_w, kw_h = self.kw_w, self.kw_h
            f_kb = np.zeros((kw_h, kw_w, 3), dtype=np.uint8)
            self.draw_glass_panel(f_kb, kw_w, kw_h, "NEURO DRISTI - TYPING STATION")
            try:
                wx2, wy2, ww2, wh2 = cv2.getWindowImageRect(self.win_kb)
                rx2, ry2 = mx - wx2, my - wy2
            except:
                wx2 = int(cv2.getWindowProperty(self.win_kb, cv2.WND_PROP_X))
                wy2 = int(cv2.getWindowProperty(self.win_kb, cv2.WND_PROP_Y))
                rx2, ry2 = mx - wx2, my - (wy2 + 32)
            
            if 0 < rx2 < kw_w and 0 < ry2 < kw_h:
                cv2.circle(f_kb, (rx2, ry2), 4, (255, 255, 0), -1)

            tx_x, tx_y, tx_w, tx_h = 10, 45, 700, 65
            cv2.rectangle(f_kb, (tx_x, tx_y), (tx_x + tx_w, tx_y + tx_h), (0, 0, 0), -1)
            cv2.putText(f_kb, self.keyboard_text + "|", (tx_x + 15, tx_y + 45), 0, 0.95, (255,255,255), 2)
            
            kb_sx, kb_sy = 9, 130
            k_w, k_h = 64, 52
            gap = 7
            for r, row in enumerate(self.kb_rows):
                for c, val in enumerate(row):
                    kx, ky, kw = kb_sx + (c * (k_w + gap)), kb_sy + (r * (k_h + gap)), k_w
                    if r == 4:
                        if val == 'SPACE': kw = (k_w * 5) + (gap * 4)
                        elif val == 'ENTER': kx, kw = kb_sx + (5 * (k_w + gap)), (k_w * 3) + (gap * 2)
                        elif val == 'EXIT': kx, kw = kb_sx + (8 * (k_w + gap)), (k_w * 2) + (gap * 1)
                    
                    is_h = (kx < rx2 < kx + kw) and (ky < ry2 < ky + k_h)
                    if is_h and trigger_click:
                        if val == 'BS': self.keyboard_text = self.keyboard_text[:-1]
                        elif val == 'CLR': self.keyboard_text = ""
                        elif val == 'SPACE': self.keyboard_text += " "
                        elif val == 'ENTER': self.speak(self.keyboard_text)
                        elif val == 'EXIT': os._exit(0)
                        else: self.keyboard_text += val
                    
                    btn_c = (50, 50, 50)
                    if val in ['BS', 'CLR']: btn_c = (50, 50, 90)
                    if val == 'ENTER': btn_c = (0, 90, 0)
                    self.draw_button(f_kb, kx, ky, kw, k_h, val, is_h, btn_c)

            cv2.imshow(self.win_ctrl, f_ctrl)
            cv2.imshow(self.win_kb, f_kb)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27: os._exit(0)
            
            try:
                if cv2.getWindowProperty(self.win_ctrl, cv2.WND_PROP_VISIBLE) < 1: os._exit(0)
            except: os._exit(0)

        cap.release()
        cv2.destroyAllWindows()
        self.detector.close()

def main():
    # Make sure face landmarker model is available
    check_and_download_model()
    
    # Initial Splash/Dashboard
    root = tk.Tk()
    app_engine = NeuroDristi()
    
    def start_tracking():
        root.withdraw() # Hide dashboard
        app_engine.run_tracking() # Start primary app
        root.destroy() # Close completely after tracking exits

    Dashboard(root, start_tracking)
    root.mainloop()

if __name__ == "__main__":
    main()