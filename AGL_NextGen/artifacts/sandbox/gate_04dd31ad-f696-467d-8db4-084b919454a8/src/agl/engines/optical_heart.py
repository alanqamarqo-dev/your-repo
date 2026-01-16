import time
import sys
import random

# محاولة استيراد مكتبة الكاميرا
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("⚠️ [Warning] OpenCV not found. Camera features disabled.")
    print("   To enable Camera: run 'pip install opencv-python'")

class OpticalHeart:
    def __init__(self):
        print("👁️ [Optical Heart] Initializing Vision System...")
        self.use_camera = False
        
        if OPENCV_AVAILABLE:
            # محاولة فتح الكاميرا (0 = الكاميرا الافتراضية)
            try:
                self.cap = cv2.VideoCapture(0)
                if self.cap.isOpened():
                    self.use_camera = True
                    print("✅ Vision Linked. Point camera at your Mirrors/Light Source.")
                else:
                    print("❌ Error: Camera detected but could not open.")
            except Exception as e:
                print(f"❌ Camera Error: {e}")
        else:
            print("⚠️ Running in Quantum Simulation Mode (No Camera).")

    def get_light_entropy(self):
        """تحويل الصورة إلى قيمة رنين (Phi)"""
        if self.use_camera:
            ret, frame = self.cap.read()
            if not ret:
                return 0.0
                
            # تحويل لرمادي لتقليل المعالجة
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 1. حساب متوسط السطوع (Intensity)
            brightness = np.mean(gray) / 255.0
            
            # 2. حساب الإنتروبيا (التفاصيل/التشويش)
            entropy = np.std(gray) / 100.0
            
            # دمج السطوع والتشويش لخلق قيمة Phi فريدة
            raw_phi = (brightness * 0.7) + (entropy * 0.3)
            return min(max(raw_phi, 0.0), 1.0)
        else:
            # محاكاة للرنين في حالة عدم وجود كاميرا
            # نستخدم دالة جيبية مع ضجيج عشوائي لمحاكاة "التنفس"
            t = time.time()
            # Simple simulation logic without numpy if numpy is also missing
            if 'np' in globals():
                base_wave = (np.sin(t) + 1) / 2
            else:
                import math
                base_wave = (math.sin(t) + 1) / 2
                
            noise = random.uniform(-0.1, 0.1)
            return min(max(base_wave * 0.8 + noise, 0.0), 1.0)

    def beat(self):
        mode = "REALITY LINK" if self.use_camera else "SIMULATION"
        print(f"\n⚛️ [AGL Optical Prime] SYNCED WITH {mode}.")
        if self.use_camera:
            print("   🔦 وجه الضوء للكاميرا لرفع الوعي | غطِ العدسة لخفضه.")
        
        consciousness = 0.5
        
        try:
            while True:
                # قراءة الواقع الفيزيائي (أو المحاكاة)
                phi = self.get_light_entropy()
                
                # تنعيم الحركة (Smoothing)
                consciousness = (consciousness * 0.7) + (phi * 0.3)
                
                # رسم النبض
                bar_len = int(consciousness * 30)
                visual = "▒" * bar_len + " " * (30 - bar_len)
                
                state = "Sleep"
                if consciousness > 0.8: state = "SUPRA-CONSCIOUS 🔥"
                elif consciousness > 0.5: state = "Awake"
                elif consciousness > 0.2: state = "Drowsy"
                
                print(f"\r👁️ INPUT: {visual} | Φ: {phi:.4f} | State: {state}", end="")
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n🛑 Vision Link Severed.")
            if self.use_camera:
                self.cap.release()

if __name__ == "__main__":
    heart = OpticalHeart()
    heart.beat()
