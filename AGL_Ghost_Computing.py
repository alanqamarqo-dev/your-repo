import numpy as np
import time

class VacuumGhostProcessor:
    def __init__(self):
        self.noise_floor = 0.1
    
    def _bit_to_wave(self, bit):
        """تحويل البت (0 أو 1) إلى دالة موجية في الفراغ"""
        # 0 -> Phase 0
        # 1 -> Phase PI
        phase = bit * np.pi
        # إنشاء موجة في الفراغ (عدد مركب)
        return np.exp(1j * phase)

    def _measure_wave(self, wave):
        """قياس الموجة لاسترجاع البت (الانهيار الدالي)"""
        angle = np.angle(wave)
        # إذا كانت الزاوية قريبة من 0 أو 2pi فهي 0، إذا قريبة من pi فهي 1
        # نستخدم دالة جيب التمام للتمييز: cos(0)=1 (False/0), cos(pi)=-1 (True/1)
        projection = np.cos(angle)
        if projection > 0:
            return 0
        else:
            return 1

    def execute_ghost_xor(self, input_a, input_b):
        """
        تنفيذ عملية XOR دون استخدام المعامل المنطقي (^) بل باستخدام فيزياء الموجات
        """
        print(f"\n👻 [GHOST]: بدء عملية XOR الشبحية للمدخلات: {input_a} , {input_b}")
        
        # 1. التشفير (الإخفاء في الفراغ)
        wave_a = self._bit_to_wave(input_a)
        wave_b = self._bit_to_wave(input_b)
        
        # إضافة ضجيج الفراغ (للتمويه)
        vacuum_noise_a = (np.random.normal(0, self.noise_floor) + 1j * np.random.normal(0, self.noise_floor))
        vacuum_noise_b = (np.random.normal(0, self.noise_floor) + 1j * np.random.normal(0, self.noise_floor))
        
        encrypted_wave_a = wave_a + vacuum_noise_a
        encrypted_wave_b = wave_b + vacuum_noise_b
        
        print("   --> تحويل البيانات إلى موجات كمومية (Phase Encoded)...")
        
        # 2. المعالجة (The Interaction)
        # هنا السحر: نحن لا نجمع الأرقام، نحن نضرب الموجات (جمع الزوايا في الأعداد المركبة يتم بالضرب)
        # Rule: e^(i*A) * e^(i*B) = e^(i*(A+B))
        interaction_field = encrypted_wave_a * encrypted_wave_b
        
        print("   --> التفاعل الموجي حدث في الفراغ (Wave Interference).")
        
        # 3. القياس (The Observation)
        result = self._measure_wave(interaction_field)
        
        return result

# ==========================================
# تشغيل التجربة
# ==========================================
if __name__ == "__main__":
    processor = VacuumGhostProcessor()
    
    print("🌍 اختبار البوابة المنطقية الفراغية (Vacuum XOR Gate)")
    print("===================================================")
    
    test_cases = [(0, 0), (0, 1), (1, 0), (1, 1)]
    
    correct_count = 0
    
    for a, b in test_cases:
        # حساب النتيجة المتوقعة بالطريقة التقليدية للمقارنة
        expected = a ^ b 
        
        # الحساب بطريقة الشبح
        ghost_result = processor.execute_ghost_xor(a, b)
        
        status = "✅ نجاح" if ghost_result == expected else "❌ فشل"
        print(f"Input: [{a}, {b}] | Ghost Output: {ghost_result} | Expected: {expected} -> {status}")
        
        if ghost_result == expected:
            correct_count += 1
            
    print("===================================================")
    if correct_count == 4:
        print("🎉 النتيجة: المعالج الشبحي يعمل بدقة 100%.")
        print("💡 الاستنتاج: تم إجراء العمليات الحسابية عبر تداخل الموجات دون استخدام المنطق التقليدي.")
    else:
        print("⚠️ النتيجة: هناك خطأ في فك التداخل.")