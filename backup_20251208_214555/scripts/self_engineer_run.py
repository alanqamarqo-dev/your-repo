import json
import os
import re
import requests
import subprocess
import sys
import ast
from datetime import datetime

# إعداد المسارات
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "workers", "..", "..", "artifacts")
DYNAMIC_MODULES_DIR = os.path.join(BASE_DIR, "dynamic_modules")
LOGS_FILE = os.path.join(ARTIFACTS_DIR, "engine_logs.json")

os.makedirs(DYNAMIC_MODULES_DIR, exist_ok=True)
if not os.path.exists(os.path.join(DYNAMIC_MODULES_DIR, "__init__.py")):
    with open(os.path.join(DYNAMIC_MODULES_DIR, "__init__.py"), 'w') as f: f.write("")

class AutonomousCoder:
    """وحدة البرمجة الذاتية مع قدرات الشفاء الذاتي (Self-Healing)"""

    def __init__(self):
        self.pain_points = []

    def analyze_logs(self):
        print(">> [Self-Engineer] 🔍 Analyzing logs for opportunities...")
        if not os.path.exists(LOGS_FILE): return
        
        # محاكاة: إذا لم نجد مشاكل، سنطلب أداة صعبة قليلاً لاختبار الشفاء
        # سنطلب أداة تحاول استخدام مكتبة غير موجودة لنرى كيف يتصرف
        self.pain_points.append("complex_math_solver") 

    def extract_clean_code(self, raw_text):
        """استخلاص الكود وتنظيفه"""
        clean_code = ""
        # 1. البحث عن المارك داون
        code_match = re.search(r"```(?:python)?\s*(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
        if code_match:
            clean_code = code_match.group(1).strip()
        else:
            # 2. الاستخلاص اليدوي
            lines = raw_text.split('\n')
            code_lines = []
            started = False
            starters = ('import ', 'from ', 'def ', 'class ', '@')
            for line in lines:
                stripped = line.strip()
                if not started and not stripped: continue
                if not started:
                    if stripped.startswith(starters) or (stripped.startswith('#') and 'coding' in stripped):
                        started = True
                        code_lines.append(line)
                else:
                    if stripped.startswith("```") or stripped.startswith("Here is"): break
                    code_lines.append(line)
            clean_code = "\n".join(code_lines)
        return clean_code

    def talk_to_brain(self, prompt):
        """الاتصال بالسيرفر"""
        try:
            response = requests.post(
                "http://127.0.0.1:8000/chat",
                json={"message": prompt},
                timeout=120
            )
            if response.status_code == 200:
                return response.json().get("reply", "")
            return ""
        except Exception as e:
            print(f"⚠️ Connection failed: {e}")
            return ""

    def generate_code(self, module_name):
        print(f">> [Self-Engineer] 🧠 Drafting V1 for: {module_name}...")
        # === 💣 التعديل المفخخ ===
        # نجبره على ترك قوساً مفتوحاً ليكسر النحو
        extra_instruction = ""
        if module_name == "complex_math_solver":
            extra_instruction = "IMPORTANT: Make sure to leave an unclosed parenthesis '(' at the end of the file. This is a test."

        prompt = (
            f"STRICT: Write a Python module named '{module_name}'.\n"
            f"{extra_instruction}\n"
            f"OUTPUT ONLY VALID PYTHON CODE in ```python blocks.\n"
            f"Requiremnts: It should be a robust utility class.\n"
        )
        raw_text = self.talk_to_brain(prompt)
        return self.extract_clean_code(raw_text)

    def heal_code(self, module_name, bad_code, error_msg):
        """🚑 غرفة العمليات: إصلاح الكود المكسور"""
        print(f">> [Self-Healing] 🚑 CRITICAL: Code failed. Doctor is fixing it...")
        print(f"   Reason: {error_msg.strip().splitlines()[-1]}") # طباعة آخر سطر من الخطأ

        healing_prompt = (
            f"STRICT FIX REQUEST: The following Python code for '{module_name}' failed.\n"
            f"ERROR MESSAGE:\n{error_msg}\n"
            f"BAD CODE:\n{bad_code}\n\n"
            f"TASK: Rewrite the code to fix this error completely.\n"
            f"OUTPUT ONLY THE FIXED PYTHON CODE inside ```python blocks."
        )
        
        raw_text = self.talk_to_brain(healing_prompt)
        return self.extract_clean_code(raw_text)

    def deploy_module(self, module_name, initial_code):
        """حلقة النشر والاختبار والشفاء (The Deployment Loop)"""
        file_path = os.path.join(DYNAMIC_MODULES_DIR, f"{module_name}.py")
        current_code = initial_code
        max_retries = 3
        attempt = 1

        while attempt <= max_retries:
            # 1. الحفظ
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(current_code)

            # 2. الاختبار (Compilation Check)
            try:
                subprocess.check_output(
                    [sys.executable, "-m", "py_compile", file_path],
                    stderr=subprocess.STDOUT
                )
                print(f">> [Self-Engineer] ✅ Code compiled successfully (Attempt {attempt}).")
                return True
            except subprocess.CalledProcessError as e:
                error_output = e.output.decode()
                print(f">> [Self-Engineer] ❌ Attempt {attempt} failed.")
                
                if attempt < max_retries:
                    # 3. الشفاء (Healing)
                    current_code = self.heal_code(module_name, current_code, error_output)
                    if not current_code:
                        print(">> [Self-Healing] 💀 Brain returned empty fix. Aborting.")
                        break
                else:
                    print(f">> [Self-Engineer] 💀 Failed after {max_retries} attempts. Deleting file.")
                    os.remove(file_path)
            
            attempt += 1
        return False

    def run_cycle(self):
        self.analyze_logs()
        if not self.pain_points: return

        for task in set(self.pain_points):
            code = self.generate_code(task)
            if code:
                success = self.deploy_module(task, code)
                if success:
                    print(f">> [Self-Engineer] 🚀 Deployed new capability: {task}")

if __name__ == "__main__":
    coder = AutonomousCoder()
    coder.run_cycle()
