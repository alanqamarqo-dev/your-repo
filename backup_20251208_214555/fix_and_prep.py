import os
import re
import shutil
import codecs
import sys

# المجلدات التي سيتم تجاهلها
IGNORE_DIRS = {'.git', '__pycache__', 'venv', '.venv', 'logs', 'artifacts'}

# خريطة لترجمة أسماء الاستيراد إلى أسماء حزم pip
LIB_MAPPING = {
    'sklearn': 'scikit-learn',
    'cv2': 'opencv-python',
    'PIL': 'Pillow',
    'yaml': 'PyYAML',
    'bs4': 'beautifulsoup4',
    'tensorflow': 'tensorflow',
    'torch': 'torch',
    'transformers': 'transformers',
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'faiss': 'faiss-cpu' # نبدأ بـ CPU للأمان
}

def clean_file_encoding(file_path):
    """يزيل BOM ويصلح الترميز ويحفظ نسخة احتياطية."""
    try:
        # 1. قراءة الملف كـ Bytes للكشف عن BOM
        with open(file_path, 'rb') as f:
            content_bytes = f.read()

        has_bom = content_bytes.startswith(codecs.BOM_UTF8)
        
        if has_bom:
            print(f"🔧 Fixing BOM in: {os.path.relpath(file_path)}")
            content = content_bytes.decode('utf-8-sig') # قراءة مع إزالة BOM
            
            # إنشاء نسخة احتياطية
            shutil.copy(file_path, file_path + ".bak")
            
            # إعادة الكتابة بترميز نظيف
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}")
        return False

def scan_imports(root_dir):
    """يستخرج المكتبات المطلوبة من الكود."""
    found_imports = set()
    
    print("\n📦 Scanning for dependencies...")
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # تجاهل المجلدات غير المهمة
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        
        for filename in filenames:
            if filename.endswith(".py"):
                path = os.path.join(dirpath, filename)
                clean_file_encoding(path) # إصلاح الترميز أثناء المسح
                
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        # البحث عن import X أو from X import Y
                        imports = re.findall(r'^(?:from|import)\s+([a-zA-Z0-9_]+)', content, re.MULTILINE)
                        found_imports.update(imports)
                except Exception:
                    pass

    return found_imports

def generate_requirements(imports):
    """ينشئ ملف requirements.txt."""
    reqs = set()
    # قائمة ببعض المكتبات القياسية المعروفة لتجاهلها
    std_libs = {'os', 'sys', 're', 'json', 'time', 'datetime', 'math', 'random', 
                'subprocess', 'threading', 'asyncio', 'collections', 'typing', 'ast', 
                'shutil', 'logging', 'sqlite3', 'pickle', 'codecs', 'copy'}

    for lib in imports:
        if lib in std_libs:
            continue
        
        # تحويل الاسم إذا كان معروفاً، وإلا استخدامه كما هو
        pip_name = LIB_MAPPING.get(lib, lib)
        reqs.add(pip_name)

    out_path = os.path.join(os.getcwd(), "requirements_generated.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        for r in sorted(reqs):
            f.write(f"{r}\n")
    
    print(f"\n✅ Generated '{out_path}' with {len(reqs)} packages.")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"🚀 Starting System Cleanup in: {current_dir}")
    
    found = scan_imports(current_dir)
    generate_requirements(found)
    
    print("\n🎉 Cleanup Complete. Next Steps:")
    print("1. Review 'requirements_generated.txt'")
    print("2. Run: pip install -r requirements_generated.txt")
    print("3. Run: python order_scanner.py (to verify fixes)")
