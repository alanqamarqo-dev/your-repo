#!/usr/bin/env python3
import os
import sys

target_file = "server_fixed.py"

script_dir = os.path.dirname(os.path.abspath(__file__))

# Look for target_file in multiple likely locations: next to this script,
# in the repo root, or in the current working directory (caller).
candidate_paths = [
    os.path.join(script_dir, target_file),
    os.path.join(script_dir, '..', target_file),
    os.path.join(os.getcwd(), target_file),
    os.path.join(os.getcwd(), 'repo-copy', target_file),
]

found_path = None
for p in candidate_paths:
    p_norm = os.path.normpath(p)
    if os.path.exists(p_norm):
        found_path = p_norm
        break

if not found_path:
    print(f"🔧 جاري إصلاح تحميل العقل في {target_file}...")
    print(f"❌ لم يتم العثور على الملف {target_file} في المواقع المتوقعة:\n  " + "\n  ".join(candidate_paths))
    sys.exit(1)

print(f"🔧 جاري إصلاح تحميل العقل في {found_path}...")

try:
    with open(found_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    imports_added = False
    brain_loaded = False

    for line in lines:
        # 1. إضافة استيراد العقل في البداية إذا لم يكن موجوداً
        if "import" in line and not imports_added:
            new_lines.append(line)
            if "from Core_Engines.Quantum_Neural_Core" not in "".join(lines):
                new_lines.append("from Core_Engines.Quantum_Neural_Core import QuantumNeuralCore\n")
                new_lines.append("print('🧠 [Patch] QuantumNeuralCore imported.')\n")
            imports_added = True
            continue

        # 2. البحث عن تهيئة التطبيق (app = FastAPI)
        if "app = FastAPI" in line:
            new_lines.append(line)
            # إضافة كود تحميل العقل مباشرة بعد إنشاء التطبيق
            new_lines.append("\n# --- FORCED BRAIN LOAD (PATCH) ---\n")
            new_lines.append("try:\n")
            new_lines.append("    print('⏳ [Patch] Forcing Brain Load...')\n")
            new_lines.append("    global AGI_BRAIN\n")
            new_lines.append("    AGI_BRAIN = QuantumNeuralCore()\n")
            new_lines.append("    print('✅ [Patch] Brain Loaded Successfully!')\n")
            new_lines.append("except Exception as e:\n")
            new_lines.append("    print(f'❌ [Patch] Failed to load brain: {e}')\n")
            new_lines.append("    AGI_BRAIN = None\n")
            new_lines.append("# ---------------------------------\n")
            brain_loaded = True
            continue

        new_lines.append(line)

    # كتابة الملف المعدل (نستخدم المسار المكتشف)
    with open(found_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("✅ تم تعديل server_fixed.py بنجاح.")
    print("🚀 الآن أعد تشغيل السيرفر وسيعمل العقل فوراً.")

except FileNotFoundError:
    print(f"❌ لم يتم العثور على الملف {target_file}")
