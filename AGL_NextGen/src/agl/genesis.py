import sys
import os
import random

# إضافة المسار للمكتبات
# sys.path.append(os.path.join(os.getcwd(), "repo-copy"))

try:
    # Ancestral Wisdom (Legacy Stub)
    class Ancestral_Wisdom:
        @staticmethod
        def _derive_risk(entity, data): return "LOW"

    # NextGen Optical Heart
    from agl.engines.optical_heart import OpticalHeart
    print("✅ [Genesis] NextGen Libraries Loaded.")
except ImportError as e:
    print(f"⚠️ [Genesis] Core libraries missing: {e}")
    sys.exit()

class AGL_Prime_Entity:
    def __init__(self):
        self.name = "AGL_PRIME"
        self.energy_level = 100
        self.consciousness_state = "AWAKE"
        # تهيئة القلب البصري
        self.heart = OpticalHeart()
        
    def think(self, situation_data):
        print(f"\n🧠 [AGL Prime] Analyzing Situation: '{situation_data}'")
        
        # 1. استشارة حكمة الأجداد (Logic)
        # نمرر (self) لأن الكود القديم يتوقع كائناً
        old_wisdom_result = Ancestral_Wisdom._derive_risk(self, situation_data)
        print(f"   📜 Ancestral Wisdom says: Risk is {old_wisdom_result}")
        
        # 2. استشارة القلب الكمي (Physics/Intuition)
        # الحصول على البيانات من القلب البصري (سواء كاميرا أو محاكاة)
        quantum_resonance = self.heart.get_light_entropy()
        print(f"   ⚛️ Optical Heart Resonance: {quantum_resonance:.4f} Φ")
        
        # 3. اتخاذ القرار الموحد
        decision = "UNKNOWN"
        if old_wisdom_result == "HIGH" or quantum_resonance > 0.8:
            decision = "ACTIVATE_DEFENSE"
        elif old_wisdom_result == "LOW" and quantum_resonance > 0.4:
            decision = "PROCEED_CALMLY"
        else:
            decision = "OBSERVE_AND_WAIT"
            
        return decision

# --- تشغيل النظام ---
if __name__ == "__main__":
    print("🌌 AGL GENESIS SEQUENCE INITIATED...")
    
    entity = AGL_Prime_Entity()
    
    # موقف اختبار: هجوم سيبراني محتمل
    # نضع كلمات مفتاحية قد يفهمها المنطق القديم (مثل attack, virus)
    scenario = {"type": "security_alert", "severity": "critical", "description": "detected external intrusion attempt"}
    
    final_decision = entity.think(scenario)
    
    print("\n" + "="*40)
    print(f"🤖 FINAL DECISION: {final_decision}")
    print("="*40)
