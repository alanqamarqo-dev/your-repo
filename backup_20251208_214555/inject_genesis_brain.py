import os

# كود "العقل" المحدث الذي يدمج قدرات Genesis Alpha مع الهيكلة الجديدة
new_quantum_core_code = """
import json
import os
import requests
import time
from dotenv import load_dotenv

# تحميل الإعدادات من ملف .env الذي أنشأناه سابقاً
load_dotenv()

class QuantumNeuralCore:
    def __init__(self):
        self.name = "QuantumCore"
        self.status = "active"
        # استدعاء الإعدادات من البيئة
        self.llm_base_url = os.getenv("AGL_LLM_BASEURL", "http://localhost:11434/v1")
        self.model = os.getenv("AGL_LLM_MODEL", "qwen2.5:7b-instruct")
        self.context = "Genesis_Alpha"
        
    def collapse_wave_function(self, prompt_input):
        '''
        هذه الدالة هي التي تقوم بعملية 'التفكير العميق' باستخدام LLM
        وتحاكي منطق Genesis Alpha الذي أظهرته في السجلات.
        '''
        print(f"   [Quantum Core] 🌌 Collapsing wave function for: {prompt_input[:30]}...")
        
        # صياغة البرومبت الخاص بـ Genesis Alpha
        system_prompt = (
            f"You are the Core Intelligence of AGL, operating in phase '{self.context}'. "
            "Analyze the input deeply. "
            "Return your response in STRICT JSON format with keys: 'hypothesis', 'confidence', 'reasoning', 'next_step'."
        )
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_input}
            ],
            "temperature": 0.7,
            "stream": False
        }
        
        try:
            # الاتصال بـ Ollama
            response = requests.post(f"{self.llm_base_url}/chat/completions", json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                # محاولة استخراج JSON من الرد
                try:
                    # تنظيف النص لاستخراج JSON فقط
                    json_str = content
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        json_str = content.split("```")[1].split("```")[0].strip()
                        
                    parsed_result = json.loads(json_str)
                    
                    # إضافة طابع Genesis Alpha
                    final_output = {
                        "engine": "QuantumCore",
                        "genesis_phase": self.context,
                        "thought_process": parsed_result,
                        "raw_output": content,
                        "timestamp": time.time()
                    }
                    print("   [Quantum Core] ✅ Wave function collapsed successfully.")
                    return final_output
                    
                except json.JSONDecodeError:
                    # في حالة فشل الـ JSON، نرجع النص الخام
                    return {"engine": "QuantumCore", "output": content, "mode": "raw_thought"}
            else:
                print(f"   [Quantum Core] ⚠️ Connection Error: {response.status_code}")
                return {"engine": "QuantumCore", "error": "LLM_Connection_Failed"}
                
        except Exception as e:
            print(f"   [Quantum Core] ❌ Error: {str(e)}")
            # Fallback (التعافي الذاتي البسيط)
            return {"engine": "QuantumCore", "error": str(e), "fallback_mode": "active"}

    def process(self, data):
        # هذه الواجهة لضمان التوافق مع Mission Control
        input_text = data if isinstance(data, str) else str(data)
        return self.collapse_wave_function(input_text)
"""

# كتابة الملف في المسار الصحيح
target_path = "Core_Engines/Quantum_Neural_Core.py"
os.makedirs("Core_Engines", exist_ok=True)

with open(target_path, "w", encoding="utf-8") as f:
    f.write(new_quantum_core_code)

print("=========================================")
print("💉 تمت عملية الحقن بنجاح!")
print(f"🧠 تم دمج عقل Genesis Alpha داخل: {target_path}")
print("🚀 الآن نظام Mission Control سيستخدم الذكاء الحقيقي لـ Qwen.")
print("=========================================")
