import os

# كود التحكم الجديد الذي يجبر النظام على استخدام الذكاء الحقيقي
real_mission_control_code = '''
import sys
import os
import time
from dotenv import load_dotenv

# إضافة المجلد الرئيسي للمسار لنتمكن من استيراد المحركات
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Core_Engines.Quantum_Neural_Core import QuantumNeuralCore

# تحميل الإعدادات
load_dotenv()

def run_real_mission():
    # تهيئة العقل
    brain = QuantumNeuralCore()
    
    print("🎮 [Mission Control] System Online: Genesis_Alpha")
    print(f"🔌 Connected to: {brain.model} @ {brain.llm_base_url}")
    
    # المهمة التي طلبتها
    mission_prompt = "احسب انتروبيا ثقب أسود (فيزياء)، ثم اكتب كود محاكاة بايثون بسيط له."
    
    print(f"🚀 Mission: {mission_prompt}")
    print("⏳ Connecting to Neural Core... (This relies on your Local LLM)")
    
    # 1. المرحلة العلمية (الفيزياء)
    print("\n📍 Phase 1: Deep Physics Analysis...")
    physics_prompt = f"قم بتحليل فيزيائي عميق للمهمة التالية: {mission_prompt}. اشرح المعادلات والمفاهيم."
    physics_result = brain.process(physics_prompt)
    
    if "thought_process" in physics_result:
        print(f"💡 Quantum Thought: {physics_result['thought_process']}")
    elif "output" in physics_result:
        print(f"📝 Analysis Result:\n{physics_result['output']}")
    
    # 2. المرحلة البرمجية (الكود)
    print("\n📍 Phase 2: Generating Simulation Code...")
    code_prompt = f"بناءً على التحليل السابق، اكتب كود Python كامل لمحاكاة {mission_prompt}. اجعل الكود احترافياً وعملياً."
    code_result = brain.process(code_prompt)
    
    if "output" in code_result:
        print(f"💻 Generated Code:\n{code_result['output']}")
    else:
        print(code_result)

    print("\n✅ Mission Complete: Real Intelligence Used.")

if __name__ == "__main__":
    run_real_mission()
'''

target_file = "dynamic_modules/mission_control.py"

# التأكد من وجود المجلد
os.makedirs("dynamic_modules", exist_ok=True)

# كتابة الكود الجديد
with open(target_file, "w", encoding="utf-8") as f:
    f.write(real_mission_control_code)

print("✅ تم تحديث mission_control.py بنجاح.")
print("🧠 النظام الآن مجبر على استخدام QuantumCore (Genesis Alpha).")
print("🚀 شغّل: python dynamic_modules/mission_control.py واستمتع بالنتيجة الحقيقية.")
