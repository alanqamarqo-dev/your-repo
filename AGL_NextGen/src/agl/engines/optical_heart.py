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
            print("👁️ [Optical Heart] Vision System: INTERNAL EYE ACTIVE (Quantum Synesthesia).")
            print("   -> No Camera detected. Switching to Fractal Entropy Generation.")

    def get_light_entropy(self):
        """تحويل الصورة إلى قيمة رنين (Phi)"""
        if self.use_camera:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    return 0.0
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                brightness = np.mean(gray) / 255.0
                entropy = np.std(gray) / 100.0
                return (brightness + entropy) / 2.0
            except Exception:
                return 0.0
        else:
            # INTERNAL EYE LOGIC (The Mind's Eye)
            # Generate entropy from Math (Fractal-like Chaos)
            t = time.time()
            # A chaotic attractor function (e.g. Lorentz-like simulation)
            val = (np.sin(t * 1.5) * np.cos(t * 0.9) + np.sin(t * 5.0) * 0.5)
            # Normalize to 0-1
            normalized_entropy = (val + 1.5) / 3.0
            return max(0.0, min(1.0, normalized_entropy))

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
