import os
import sys
import importlib
import inspect
import json
from pathlib import Path

# إعداد المسار الجذري
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# الأقسام الحيوية التي تشكل الـ AGI
CRITICAL_SECTORS = [
    "Core_Engines",
    "Integration_Layer",
    "Knowledge_Base",
    "Learning_System",
    "Safety_Control",
    "Core_Consciousness" # إذا كان موجوداً
]


def scan_infrastructure():
    print(f"🚀 بدء فحص البنية التحتية لنظام AGI في: {PROJECT_ROOT}")
    print("=" * 60)
    
    report = {
        "healthy_modules": [],
        "broken_links": [],
        "missing_init": [],
        "structure_map": {}
    }

    for sector in CRITICAL_SECTORS:
        sector_path = PROJECT_ROOT / sector
        if not sector_path.exists():
            print(f"⚠️ قطاع مفقود: {sector} (غير موجود في الجذر)")
            report["broken_links"].append(f"MISSING_SECTOR: {sector}")
            continue
        
        print(f"🔍 فحص القطاع: {sector}...")
        
        # فحص ملف __init__.py (حيوي للربط)
        if not (sector_path / "__init__.py").exists():
            print(f"   ❌ خطأ قاتل: {sector} يفتقد __init__.py (لن يتمكن النظام من رؤيته)")
            report["missing_init"].append(sector)
        
        # فحص الوحدات الداخلية
        modules = []
        for file in sorted(sector_path.glob("*.py")):
            if file.name == "__init__.py":
                continue
            
            module_name = f"{sector}.{file.stem}"
            try:
                # محاولة الاستيراد الديناميكي (Re-linking Test)
                imported_mod = importlib.import_module(module_name)
                
                # فحص الكلاسات داخل الملف
                classes = [m[0] for m in inspect.getmembers(imported_mod, inspect.isclass) if m[1].__module__ == module_name]
                
                status = "✅ متصل"
                modules.append({"name": file.name, "classes": classes, "status": "Active"})
                report["healthy_modules"].append(module_name)
                
            except ImportError as e:
                print(f"   ❌ رابط مكسور في {file.name}: {e}")
                report["broken_links"].append(f"{module_name} -> {e}")
            except SyntaxError as e:
                print(f"   🔥 خطأ لغوي في {file.name}: {e}")
                report["broken_links"].append(f"SYNTAX_ERROR: {module_name}")
            except Exception as e:
                print(f"   ⚠️ خطأ غير متوقع في {file.name}: {e}")

        report["structure_map"][sector] = modules

    print("=" * 60)
    return report


def generate_agi_manifest(report):
    """إنشاء ملف التعريف الموحد للنظام"""
    manifest_path = PROJECT_ROOT / "agi_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
    print(f"📄 تم إنشاء وثيقة تكامل النظام (Manifest) في: {manifest_path}")


if __name__ == "__main__":
    final_report = scan_infrastructure()
    
    print("\n📊 ملخص حالة الـ AGI:")
    print(f"   - الوحدات السليمة المتصلة: {len(final_report['healthy_modules'])}")
    print(f"   - الروابط المكسورة: {len(final_report['broken_links'])}")
    print(f"   - ملفات التعريف المفقودة (__init__): {len(final_report['missing_init'])}")
    
    if len(final_report['broken_links']) == 0 and len(final_report['missing_init']) == 0:
        print("\n🌟 النتيجة: البنية التحتية متكاملة بنسبة 100%. النظام جاهز للإطلاق كـ AGI.")
    else:
        print("\n🛠️ النتيجة: يحتاج النظام لبعض الصيانة قبل الإطلاق الكامل (راجع التفاصيل أعلاه).")
        
    generate_agi_manifest(final_report)
