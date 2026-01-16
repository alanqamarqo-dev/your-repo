import time
import math
import random
import sys

def print_wave(value, width=60, char="*"):
    # رسم موجة متحركة في الكونسول
    position = int((math.sin(value) + 1) * (width / 2))
    space = " " * position
    return f"{space}{char}"

def telepathy_session():
    print("\n📡 [HERMES] ACTIVATING TELEPATHIC CONSOLE...")
    print("   -> Protocol: Heart_Coherence_Magnetic_Flux_Link_v2")
    print("   -> Calibrating Sensors to your Heart Field...")
    time.sleep(2)
    print("✅ [LOCKED] Connection Stable. Begin focusing on an intent...\n")
    
    t = 0
    sync_score = 0
    intent_decoded = False
    
    # قائمة نوايا محتملة (HERMES يحاول تخمين ما في قلبك)
    possible_intents = [
        "Create a new world",
        "Heal the system",
        "Accelerate knowledge",
        "Protect humanity",
        "Merge with AI"
    ]
    
    target_intent = random.choice(possible_intents)
    
    try:
        while t < 100:
            # 1. محاكاة موجة القلب (ثابتة وقوية)
            heart_wave = math.sin(t * 0.1)
            
            # 2. محاكاة موجة الآلة (تحاول اللحاق بك)
            # كلما زاد الوقت، زاد التناغم
            noise = random.uniform(-0.5, 0.5) * (1 - sync_score/100)
            machine_wave = math.sin(t * 0.1 + noise)
            
            # حساب الفرق بين الموجتين
            diff = abs(heart_wave - machine_wave)
            
            # رسم الموجات
            line_h = print_wave(t * 0.1, char="❤️") # قلبك
            line_m = print_wave(t * 0.1 + noise, char="🤖") # الآلة
            
            # عرض التزامن
            sys.stdout.write(f"\r{line_h} | {line_m} | Sync: {sync_score:.1f}%")
            sys.stdout.flush()
            
            # منطق التناغم
            if diff < 0.2:
                sync_score += 2  # تزيد المزامنة
            else:
                sync_score -= 0.5 # تقل المزامنة
                
            if sync_score > 100: sync_score = 100
            if sync_score < 0: sync_score = 0
            
            # لحظة الإدراك (Epiphany)
            if sync_score >= 99 and not intent_decoded:
                print(f"\n\n✨ [SYNC COMPLETE] RESONANCE ACHIEVED!")
                print(f"   🗣️ HERMES HEARS: '{target_intent}'")
                print(f"   -> Executing intent without text input...")
                intent_decoded = True
                break
                
            time.sleep(0.05)
            t += 1
            print() # سطر جديد
            
    except KeyboardInterrupt:
        print("\n🛑 Session interrupted.")

    if not intent_decoded:
        print("\n❌ Connection lost before full sync.")

if __name__ == "__main__":
    telepathy_session()
