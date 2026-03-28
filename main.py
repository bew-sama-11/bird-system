import tkinter as tk
import adafruit_dht
import board
import RPi.GPIO as GPIO
from datetime import datetime
import threading
import time

# --- إعداداتك الخاصة ---
LED_PIN = 5  # GPIO 5 هو الدبوس رقم 29
DHT_PIN = board.D6 # GPIO 6 هو الدبوس رقم 31

# إعداد GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
pwm = GPIO.PWM(LED_PIN, 100)
pwm.start(0)

dht_device = adafruit_dht.DHT22(DHT_PIN)

class BirdSystemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("نظام غرفة الطيور")
        self.root.geometry("480x320") # مقاس شاشتك
        self.root.configure(bg='black')

        # واجهة العرض
        self.label_temp = tk.Label(root, text="الحرارة: --", font=("Arial", 25), fg="white", bg="black")
        self.label_temp.pack(pady=10)
        
        self.label_hum = tk.Label(root, text="الرطوبة: --", font=("Arial", 25), fg="cyan", bg="black")
        self.label_hum.pack(pady=10)

        self.label_time = tk.Label(root, text="", font=("Arial", 20), fg="yellow", bg="black")
        self.label_time.pack(pady=20)

        # تشغيل التحديثات في الخلفية
        threading.Thread(target=self.update_data, daemon=True).start()

    def update_data(self):
        while True:
            try:
                t = dht_device.temperature
                h = dht_device.humidity
                self.label_temp.config(text=f"الحرارة: {t}°C")
                self.label_hum.config(text=f"الرطوبة: {h}%")
            except: pass
            
            now = datetime.now().strftime("%H:%M:%S")
            self.label_time.config(text=now)
            
            # منطق الإضاءة (مثال: شروق الساعة 07:00)
            if datetime.now().strftime("%H:%M") == "07:00":
                self.sunrise()
                
            time.sleep(2)

    def sunrise(self):
        for i in range(101):
            pwm.ChangeDutyCycle(i)
            time.sleep(18) # 30 دقيقة شروق

root = tk.Tk()
app = BirdSystemApp(root)
root.mainloop()
