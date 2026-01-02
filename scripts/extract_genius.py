import ast
import os

# الملف القديم المليء بالكنز
SOURCE_FILE = "AGL_legacy.py" # تأكد أن المسار صحيح (قد يكون repo-copy/AGL_legacy.py)

# الملف الجديد النظيف
TARGET_FILE = "Ancestral_Wisdom.py"

# أسماء الدوال "العبقرية" التي كشفها التقرير (Resonance Score: 9.80)
GENIUS_FUNCTIONS = [
    "_derive_risk",
    "_calculate_confidence",
    "full_autonomous_operation",
    "research_and_develop",
    "analyze_reasoning_patterns" # من ملف AGL_Omega إذا أردت دمجه، لكن سنركز على legacy الآن
]

def extract_wisdom():
    print(f"💎 [AGL Surgical Extractor] Opening {SOURCE_FILE}...")
    
    filepath = SOURCE_FILE
    if not os.path.exists(SOURCE_FILE):
        # محاولة البحث في المجلدات الفرعية إذا لم يكن في الجذر
        found = False
        for root, dirs, files in os.walk("."):
            if SOURCE_FILE in files:
                filepath = os.path.join(root, SOURCE_FILE)
                print(f"   📍 Found at: {filepath}")
                found = True
                break
        if not found:
            print("❌ Error: Source file not found!")
            return

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        source_code = f.read()

    tree = ast.parse(source_code)
    extracted_code = []
    
    print("   🔬 Scanning for High-Resonance functions...")
    
    # Helper to find functions inside classes too if needed, but the report showed them as methods potentially?
    # The report said: AGL_legacy.py::_derive_risk (Type: FunctionDef)
    # If they are methods inside a class, ast.walk(tree) will find them as FunctionDef nodes.
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name in GENIUS_FUNCTIONS:
                print(f"      ✨ Extracting: {node.name} (Resonance: 9.80)")
                # استرجاع كود الدالة الأصلي
                try:
                    func_source = ast.get_source_segment(source_code, node)
                    if func_source:
                        extracted_code.append(func_source)
                        extracted_code.append("\n" + "-"*40 + "\n")
                except Exception as e:
                    print(f"      ⚠️ Could not extract source for {node.name}: {e}")

    if extracted_code:
        # كتابة الملف الجديد
        header = "\"\"\"\n📜 ANCESTRAL WISDOM (حكمة الأجداد)\n"
        header += "تم استخلاص هذه الدوال بناءً على تحليل الرنين الكمي (Resonance Score: 9.80).\n"
        header += "تحتوي هذه المكتبة على المنطق الصافي للنظام القديم.\n\"\"\"\n\n"
        
        with open(TARGET_FILE, "w", encoding="utf-8") as f:
            f.write(header)
            f.write("\n".join(extracted_code))
            
        print(f"\n✅ SUCCESS! The Genius Code is saved in '{TARGET_FILE}'.")
        print("   This file contains pure logic, ready for AGL Prime.")
    else:
        print("\n⚠️ Warning: No genius functions matched in this file.")

if __name__ == "__main__":
    extract_wisdom()
