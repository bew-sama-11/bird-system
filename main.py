import tkinter as tk
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
        self.root.title("Bird Control System")
        
        # تفعيل وضع ملء الشاشة وإخفاء الماوس
        self.root.attributes('-fullscreen', True)
        self.root.config(cursor="none") 
        self.root.configure(bg='#121212')

        # القيم الافتراضية (ساعة:دقيقة)
        self.sun_times = {
            "rise_h": 12, "rise_m": 0,
            "set_h": 0, "set_m": 0,
            "fade": 30
        }

        self.setup_ui()
        threading.Thread(target=self.main_loop, daemon=True).start()

    def ar_text(self, text):
        return get_display(reshape(text))

    def setup_ui(self):
        # الوقت الحالي والبيانات
        self.lbl_time = tk.Label(self.root, text="", font=("Arial", 30, "bold"), fg="#f1c40f", bg="#121212")
        self.lbl_time.pack(pady=10)

        self.lbl_climate = tk.Label(self.root, text="--", font=("Arial", 18), fg="#ecf0f1", bg="#121212")
        self.lbl_climate.pack()

        # لوحة التحكم الرئيسية
        ctrl_frame = tk.Frame(self.root, bg="#121212")
        ctrl_frame.pack(pady=15)

        # إنشاء أدوات التحكم (الشروق، الغروب، التعتيم)
        self.create_time_ctrl(ctrl_frame, "الشروق", "rise_h", "rise_m", 0)
        self.create_time_ctrl(ctrl_frame, "الغروب", "set_h", "set_m", 1)
        self.create_fade_ctrl(ctrl_frame, "التعتيم", "fade", 2)

        # زر للخروج من ملء الشاشة (للطوارئ - يختفي لاحقاً)
        tk.Button(self.root, text="X", command=self.root.destroy, bg="#c0392b", fg="white", bd=0).place(x=460, y=0)

    def create_time_ctrl(self, parent, label, h_attr, m_attr, col):
        frame = tk.Frame(parent, bg="#1e1e1e", padx=5, pady=5, highlightbackground="#34495e", highlightthickness=2)
        frame.grid(row=0, column=col, padx=8)

        tk.Label(frame, text=self.ar_text(label), fg="#3498db", bg="#1e1e1e", font=("Arial", 12, "bold")).pack()
        
        # عرض الوقت الحالي المبرمج
        time_display = tk.Frame(frame, bg="#1e1e1e")
        time_display.pack()
        
        lbl_h = tk.Label(time_display, text=f"{self.sun_times[h_attr]:02d}", font=("Arial", 16, "bold"), fg="white", bg="#1e1e1e")
        lbl_h.pack(side="left")
        tk.Label(time_display, text=":", fg="white", bg="#1e1e1e").pack(side="left")
        lbl_m = tk.Label(time_display, text=f"{self.sun_times[m_attr]:02d}", font=("Arial", 16, "bold"), fg="white", bg="#1e1e1e")
        lbl_m.pack(side="left")

        # أزرار التعديل
        btn_f = tk.Frame(frame, bg="#1e1e1e")
        btn_f.pack(pady=5)
        
        # الساعات
        tk.Button(btn_f, text="H+", command=lambda: self.update_val(h_attr, 1, 23, lbl_h), width=3).grid(row=0, column=0)
        tk.Button(btn_f, text="H-", command=lambda: self.update_val(h_attr, -1, 23, lbl_h), width=3).grid(row=1, column=0)
        # الدقائق
        tk.Button(btn_f, text="M+", command=lambda: self.update_val(m_attr, 5, 59, lbl_m), width=3).grid(row=0, column=1)
        tk.Button(btn_f, text="M-", command=lambda: self.update_val(m_attr, -5, 59, lbl_m), width=3).grid(row=1, column=1)

    def create_fade_ctrl(self, parent, label, attr, col):
        frame = tk.Frame(parent, bg="#1e1e1e", padx=5, pady=5, highlightbackground="#34495e", highlightthickness=2)
        frame.grid(row=0, column=col, padx=8)
        tk.Label(frame, text=self.ar_text(label), fg="#e67e22", bg="#1e1e1e", font=("Arial", 12, "bold")).pack()
        
        lbl = tk.Label(frame, text=str(self.sun_times[attr]), font=("Arial", 16, "bold"), fg="white", bg="#1e1e1e")
        lbl.pack()
        
        btn_f = tk.Frame(frame, bg="#1e1e1e")
        btn_f.pack()
        tk.Button(btn_f, text="+", command=lambda: self.update_val(attr, 1, 120, lbl), width=4).pack()
        tk.Button(btn_f, text="-", command=lambda: self.update_val(attr, -1, 120, lbl), width=4).pack()

    def update_val(self, attr, delta, max_val, lbl):
        new_val = self.sun_times[attr] + delta
        if new_val < 0: new_val = max_val
        elif new_val > max_val: new_val = 0
        
        self.sun_times[attr] = new_val
        lbl.config(text=f"{new_val:02d}" if "fade" not in attr else str(new_val))

    def main_loop(self):
        while True:
            now = datetime.now()
            self.lbl_time.config(text=now.strftime("%H:%M:%S"))

            try:
                t, h = dht_device.temperature, dht_device.humidity
                if t and h:
                    self.lbl_climate.config(text=f"{self.ar_text('الحرارة')}: {t}°C  |  {self.ar_text('الرطوبة')}: {h}%")
            except: pass

            # فحص المطابقة بالدقيقة والثانية
            if now.second == 0:
                if now.hour == self.sun_times["rise_h"] and now.minute == self.sun_times["rise_m"]:
                    threading.Thread(target=self.run_fade, args=("up",)).start()
                elif now.hour == self.sun_times["set_h"] and now.minute == self.sun_times["set_m"]:
                    threading.Thread(target=self.run_fade, args=("down",)).start()

            time.sleep(1)

    def run_fade(self, direction):
        steps = 100
        delay = (self.sun_times["fade"] * 60) / steps
        for i in range(steps + 1):
            level = i if direction == "up" else (steps - i)
            pwm.ChangeDutyCycle(level)
            time.sleep(delay)

if __name__ == "__main__":
    root = tk.Tk()
    app = BirdSystemApp(root)
    root.mainloop()
