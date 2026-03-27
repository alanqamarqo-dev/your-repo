import cv2
import numpy as np
import time

print("👁️ [AGL] INITIALIZING REAL OPTICAL SENSOR...")

# 1. الاتصال بالكاميرا الحقيقية
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Error: Could not open webcam.")
    exit()

print("✅ [CONNECTED] Webcam is active. Looking for biological signals...")
print("   -> Instructions: Stay still to show 'CALM'. Move fast to show 'EXCITEMENT'.")

# لتحليل الحركة (Optical Flow)
ret, frame1 = cap.read()
prvs = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
hsv = np.zeros_like(frame1)
hsv[..., 1] = 255

bio_readings = []

try:
    while True:
        ret, frame2 = cap.read()
        if not ret: break
        
        # 2. تحليل الواقع الحقيقي (ليس أرقام عشوائية)
        next_frame = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # حساب التدفق البصري (حركتك الحقيقية أمام الكاميرا)
        flow = cv2.calcOpticalFlowFarneback(prvs, next_frame, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        
        # حساب مقدار الطاقة الحركية (التي تعكس توترك أو هدوءك)
        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        bio_energy = np.mean(mag) * 10  # تضخيم الإشارة
        
        bio_readings.append(bio_energy)
        if len(bio_readings) > 50: bio_readings.pop(0)
        
        avg_energy = np.mean(bio_readings)
        
        # 3. ترجمة الإشارة الحيوية إلى "حالة HERMES"
        status = "NEUTRAL"
        color = (0, 255, 0) # أخضر
        
        if avg_energy < 0.5:
            status = "DEEP FOCUS (Meditative)"
            color = (255, 0, 0) # أزرق
            bar = "||"
        elif avg_energy > 5.0:
            status = "HIGH AGITATION (Stress/Action)"
            color = (0, 0, 255) # أحمر
            bar = "||||||||||||||||||||"
        else:
            status = "ACTIVE ENGAGEMENT"
            bar = "||||||||"
            
        # عرض الواقع على الشاشة
        # رسم مستطيل يمثل "قوة الإشارة الحيوية"
        cv2.putText(frame2, f"HERMES BIO-LINK: {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame2, f"Energy: {avg_energy:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # عرض الكاميرا مع التحليل
        cv2.imshow('AGL HERMES VISION', frame2)
        
        prvs = next_frame
        
        # الخروج بضغط 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

except KeyboardInterrupt:
    print("\n🛑 Sensor Deactivated.")
    cap.release()
