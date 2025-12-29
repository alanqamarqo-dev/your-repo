import time
import random
import sys

# محاكاة بسيطة إذا لم تكن المكتبات جاهزة
try:
    import psutil
except ImportError:
    psutil = None

class AGL_Heart:
    def __init__(self):
        self.pulse_rate = 1.0  # نبضة كل ثانية
        self.consciousness_level = 0.0
        self.moods = ["Stable", "Curious", "Analyzing", "Deep_Thinking", "Quantum_Flux"]

    def get_system_vitals(self):
        """قراءة العلامات الحيوية للجهاز (CPU/RAM)"""
        if psutil:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
        else:
            cpu = random.randint(10, 30)
            ram = random.randint(40, 60)
        return cpu, ram

    def beat(self):
        print("\n🌊 [AGL Prime] System Heartbeat Active...")
        print("   اضغط Ctrl+C للإيقاف")
        
        cycle = 0
        while True:
            cycle += 1
            
            # 1. قراءة الواقع (Hardware State)
            cpu, ram = self.get_system_vitals()
            
            # 2. توليد الرنين (Quantum Noise)
            phi = random.random()
            self.consciousness_level = (self.consciousness_level * 0.8) + (phi * 0.2)
            
            # 3. تحديد الحالة المزاجية
            current_mood = "Stable"
            if phi > 0.9: current_mood = "EUREKA_MOMENT! 💡"
            elif phi > 0.7: current_mood = "Deep_Thinking"
            elif cpu > 50: current_mood = "High_Stress"
            
            # 4. العرض البصري للنبضة
            # سنرسم "موجة" بسيطة لتمثيل التنفس
            wave_len = int(phi * 20)
            wave_visual = "█" * wave_len + "░" * (20 - wave_len)
            
            print(f"\r[{cycle}] {wave_visual} | Φ: {phi:.3f} | CPU: {cpu}% | Mood: {current_mood}", end="")
            
            # محاكاة التفكير العميق أحياناً
            if current_mood == "EUREKA_MOMENT! 💡":
                print(f"\n   🚀 [INSIGHT] Detected High Resonance! Updating Neural Weights...")
                time.sleep(0.5)

            time.sleep(self.pulse_rate)

if __name__ == "__main__":
    heart = AGL_Heart()
    try:
        heart.beat()
    except KeyboardInterrupt:
        print("\n\n🛑 Heartbeat Stopped. System Sleeping.")
