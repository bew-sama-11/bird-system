import tkinter as tk
from tkinter import ttk
import adafruit_dht
import board
import RPi.GPIO as GPIO
from datetime import datetime
import threading
import time
from arabic_reshaper import reshape
from bidi.algorithm import get_display

# --- الإعدادات الفيزيائية (توصيلاتك) ---
LED_PIN = 5   # الدبوس 29
DHT_PIN = board.D6  # الدبوس 31

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
pwm = GPIO.PWM(LED_PIN, 100)
pwm.start(0)
dht_device = adafruit_dht.DHT22(DHT_PIN)

class BirdSystemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Control Panel")
        self.root.geometry("480x320") # مقاس الشاشة
        self.root.configure(bg='#1a1a1a')

        # القيم الافتراضية
        self.sunrise_hour = 12
        self.sunset_hour = 0
        self.fade_duration = 30 # دقيقة

        self.setup_ui()
        threading.Thread(target=self.main_loop, daemon=True).start()

    def ar_text(self, text):
        """دالة لإصلاح عرض اللغة العربية"""
        reshaped = reshape(text)
        return get_display(reshaped)

    def setup_ui(self):
        # الوقت الحالي والبيانات (أعلى الواجهة)
        self.lbl_time = tk.Label(self.root, text="", font=("Arial", 25), fg="yellow", bg="#1a1a1a")
        self.lbl_time.pack(pady=5)

        self.lbl_climate = tk.Label(self.root, text="--", font=("Arial", 18), fg="white", bg="#1a1a1a")
        self.lbl_climate.pack()

        # لوحة التحكم (أزرار التعديل)
        ctrl_frame = tk.Frame(self.root, bg="#1a1a1a")
        ctrl_frame.pack(pady=10)

        # التحكم بالشروق
        self.create_control(ctrl_frame, "الشروق", "sunrise_hour", 0)
        # التحكم بالغروب
        self.create_control(ctrl_frame, "الغروب", "sunset_hour", 1)
        # التحكم بمدة التعتيم
        self.create_control(ctrl_frame, "مدة التعتيم", "fade_duration", 2)

    def create_control(self, parent, label, attr, col):
        frame = tk.Frame(parent, bg="#333", padx=5, pady=5, highlightbackground="white", highlightthickness=1)
        frame.grid(row=0, column=col, padx=5)

        tk.Label(frame, text=self.ar_text(label), fg="white", bg="#333").pack()
        
        val_lbl = tk.Label(frame, text=str(getattr(self, attr)), font=("Arial", 15, "bold"), fg="#00ff00", bg="#333")
        val_lbl.pack()

        btn_frame = tk.Frame(frame, bg="#333")
        btn_frame.pack()
        
        tk.Button(btn_frame, text="+", command=lambda: self.change_val(attr, 1, val_lbl), width=3).pack(side="left")
        tk.Button(btn_frame, text="-", command=lambda: self.change_val(attr, -1, val_lbl), width=3).pack(side="left")

    def change_val(self, attr, delta, lbl):
        new_val = getattr(self, attr) + delta
        # قيود القيم
        if "hour" in attr: new_val %= 24
        if "duration" in attr: new_val = max(1, min(120, new_val))
        
        setattr(self, attr, new_val)
        lbl.config(text=str(new_val))

    def main_loop(self):
        while True:
            # تحديث الوقت
            now = datetime.now()
            self.lbl_time.config(text=now.strftime("%H:%M:%S"))

            # قراءة الحساس
            try:
                t = dht_device.temperature
                h = dht_device.humidity
                text = f"{self.ar_text('الحرارة')}: {t}°C  |  {self.ar_text('الرطوبة')}: {h}%"
                self.lbl_climate.config(text=text)
            except: pass

            # فحص مواعيد الإضاءة
            if now.minute == 0 and now.second == 0:
                if now.hour == self.sunrise_hour:
                    self.run_fade("up")
                elif now.hour == self.sunset_hour:
                    self.run_fade("down")

            time.sleep(1)

    def run_fade(self, direction):
        step_delay = (self.fade_duration * 60) / 100
        for i in range(101):
            val = i if direction == "up" else (100 - i)
            pwm.ChangeDutyCycle(val)
            time.sleep(step_delay)

if __name__ == "__main__":
    root = tk.Tk()
    app = BirdSystemApp(root)
    root.mainloop()
