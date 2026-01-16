# استدعاء مكتبتك الخاصة
from AGL_Eyes import AGL_Retina
import cv2

# تشغيل النظام
try:
    # 1. تفعيل العين
    my_eyes = AGL_Retina()
    
    print("\n🚀 System is running on AGL_Vision Drivers.")
    print("   -> Press 'q' to exit.")

    while True:
        # 2. قراءة الواقع بكلمة واحدة فقط!
        frame, energy = my_eyes.scan_reality()
        
        if frame is None: break
        
        # 3. الحصول على الحالة
        status = my_eyes.get_vision_mode(energy)
        
        # العرض (HUD)
        # نغير اللون بناء على الطاقة (أخضر=هادئ، أحمر=قوي)
        color = (0, 255, 0)
        if energy > 3: color = (0, 0, 255)
        
        cv2.putText(frame, f"AGL FLUX: {energy:.2f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.putText(frame, f"STATUS: {status}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        
        cv2.imshow('AGL CUSTOM VISION', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    my_eyes.close()

except Exception as e:
    print(f"Error: {e}")
