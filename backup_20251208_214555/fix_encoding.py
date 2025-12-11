import os

target_file = "server_fixed.py"

print("🔧 جاري إصلاح ترميز اللغة العربية (UTF-8)...")

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# الحل: إضافة إعدادات الترميز في بداية تشغيل التطبيق
if "sys.stdout.reconfigure" not in content:
    patch_code = """
import sys
import io
# إجبار النظام على استخدام UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
"""
    # نضيف الكود بعد الـ imports
    lines = content.splitlines()
    final_lines = [lines[0]] + patch_code.splitlines() + lines[1:]
    
    with open(target_file, "w", encoding="utf-8") as f:
        f.write("\n".join(final_lines))
    print("✅ تم إضافة دعم اللغة العربية بنجاح.")
else:
    print("ℹ️ السيرفر يدعم العربية بالفعل.")

print("🚀 أعد تشغيل السيرفر الآن وجرب السؤال العربي.")
