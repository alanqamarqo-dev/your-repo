import os
import ast
import sys

def scan_directory(root_dir):
    report = []
    file_count = 0
    error_count = 0

    print(f"--- Scanning Directory: {root_dir} ---")
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # تجاهل المجلدات الافتراضية
        if '.git' in dirpath or '__pycache__' in dirpath or 'venv' in dirpath:
            continue

        for filename in filenames:
            if filename.endswith(".py"):
                file_count += 1
                full_path = os.path.join(dirpath, filename)
                
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        source = f.read()
                    
                    # 1. فحص البنية (Syntax Check)
                    ast.parse(source)
                    
                except SyntaxError as e:
                    error_count += 1
                    report.append(f"[Syntax Error] File: {filename} | Line: {e.lineno} | Msg: {e.msg}")
                except Exception as e:
                    error_count += 1
                    report.append(f"[Read Error] File: {filename} | Msg: {str(e)}")

    summary = f"\n--- Scan Summary ---\nFiles Scanned: {file_count}\nErrors Found: {error_count}"
    
    # طباعة التقرير النهائي (هذا ما سيقرأه الذكاء الاصطناعي)
    print("\n".join(report))
    print(summary)
    
    if error_count == 0:
        print("\n✅ System Integrity: HEALTHY")
    else:
        print("\n❌ System Integrity: ISSUES FOUND")

if __name__ == "__main__":
    # الفحص يبدأ من المجلد الحالي
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scan_directory(current_dir)
