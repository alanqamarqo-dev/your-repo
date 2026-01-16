
import json
import os
import requests
import time
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(): pass
from agl.lib.utils.llm_tools import build_llm_url

# تحميل الإعدادات من ملف .env الذي أنشأناه سابقاً
load_dotenv()

class QuantumNeuralCore:
    def __init__(self):
        self.name = "QuantumCore"
        self.status = "active"
        # استدعاء الإعدادات من البيئة
        self.llm_base_url = os.getenv("AGL_LLM_BASEURL", "http://localhost:11434")
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
            # الاتصال بـ Ollama (use central URL builder)
            try:
                timeout_val = int(os.getenv("AGL_HTTP_TIMEOUT", "30"))
            except Exception:
                timeout_val = 30
            # Try standard Ollama endpoint first as it is more reliable locally
            endpoint = build_llm_url('/api/chat', base=self.llm_base_url)
            try:
                response = requests.post(endpoint, json=payload, timeout=timeout_val)
            except Exception:
                response = None

            # Fallback to OpenAI compatible endpoint if 404 or connection failed
            if not response or (hasattr(response, 'status_code') and response.status_code == 404):
                 endpoint = build_llm_url('chat', base=self.llm_base_url)
                 try:
                     response = requests.post(endpoint, json=payload, timeout=timeout_val)
                 except Exception:
                     response = None

            # Fallback to /api/generate if chat endpoints fail
            if not response or (hasattr(response, 'status_code') and response.status_code == 404):
                 endpoint = build_llm_url('generate', base=self.llm_base_url)
                 # Generate endpoint expects 'prompt' not 'messages'
                 full_prompt = f"System: {system_prompt}\nUser: {prompt_input}"
                 gen_payload = {
                     "model": self.model,
                     "prompt": full_prompt,
                     "stream": False
                 }
                 try:
                     response = requests.post(endpoint, json=gen_payload, timeout=timeout_val)
                 except Exception:
                     response = None
            
            # Retry logic for 500 errors (likely OOM) or 404 (Model Not Found) or Connection Failed
            if (not response or (hasattr(response, 'status_code') and (response.status_code == 500 or response.status_code == 404))) and self.model != "qwen2.5:0.5b":
                err_code = response.status_code if response and hasattr(response, 'status_code') else 'ConnectionFailed'
                print(f"   [Quantum Core] ⚠️ Error {err_code} with {self.model}. Retrying with qwen2.5:0.5b...")
                self.model = "qwen2.5:0.5b"
                payload["model"] = "qwen2.5:0.5b"
                
                # Determine which payload to use based on endpoint
                current_payload = payload
                if "generate" in endpoint:
                     # Re-construct gen_payload with new model
                     full_prompt = f"System: {system_prompt}\nUser: {prompt_input}"
                     gen_payload = {"model": self.model, "prompt": full_prompt, "stream": False}
                     current_payload = gen_payload
                
                try:
                    response = requests.post(endpoint, json=current_payload, timeout=timeout_val)
                except Exception:
                    response = None

            if response and response.status_code == 200:
                data = response.json()
                # Handle multiple response formats (Ollama / OpenAI)
                if 'message' in data:
                    content = data['message']['content']
                elif 'choices' in data:
                    content = data['choices'][0]['message']['content']
                elif 'response' in data:
                    content = data['response']
                else:
                    content = str(data)
                
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
                        "depth": "high", # Explicitly set depth for system logs
                        "timestamp": time.time()
                    }
                    print("   [Quantum Core] ✅ Wave function collapsed successfully.")
                    return final_output
                    
                except json.JSONDecodeError:
                    # في حالة فشل الـ JSON، نرجع النص الخام
                    return {"engine": "QuantumCore", "output": content, "mode": "raw_thought", "depth": "medium"}
            else:
                err_msg = response.status_code if response and hasattr(response, 'status_code') else 'Connection_Failed'
                print(f"   [Quantum Core] ⚠️ Connection Error: {err_msg}")
                return {"engine": "QuantumCore", "error": "LLM_Connection_Failed"}
                
        except Exception as e:
            print(f"   [Quantum Core] ❌ Error: {str(e)}")
            # Fallback (التعافي الذاتي البسيط)
            return {"engine": "QuantumCore", "error": str(e), "fallback_mode": "active"}

    def process(self, data):
        # هذه الواجهة لضمان التوافق مع Mission Control
        if isinstance(data, str):
            input_text = data
        elif isinstance(data, dict):
            # استخراج النص من الـ dict
            input_text = data.get('problem', data.get('input', str(data)))
        else:
            input_text = str(data)
        return self.collapse_wave_function(input_text)

    def quantum_neural_forward(self, data):
        """Alias for process to satisfy Mission Control interface"""
        return self.process(data)
