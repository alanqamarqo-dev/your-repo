import os
import ast
import datetime

# ==============================================================================
# AGL PROJECT SCANNER - DEEP ANALYSIS TOOL
# ==============================================================================

class ProjectScanner:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.ignore_patterns = ['test', 'tests', '__pycache__', 'env', 'venv', '.git', 'build', 'dist']
        self.report_data = []

    def is_test_file(self, filepath):
        """فحص ما إذا كان الملف أو المسار خاص بالاختبارات"""
        path_parts = filepath.lower().replace('\\', '/').split('/')
        for part in path_parts:
            for pattern in self.ignore_patterns:
                if pattern in part:
                    return True
        return False

    def get_imports_and_defs(self, tree):
        """استخراج المكتبات والكلاسات والدوال باستخدام AST"""
        imports = set()
        definitions = []
        
        for node in ast.walk(tree):
            # 1. استخراج المكتبات (Imports)
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name.split('.')[0]) # أخذ الاسم الجذري للمكتبة
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
            
            # 2. استخراج التعريفات (Classes & Functions)
            elif isinstance(node, ast.ClassDef):
                definitions.append(f"Class: {node.name}")
            elif isinstance(node, ast.FunctionDef):
                # نأخذ فقط الدوال الرئيسية (ليست داخل دوال أخرى) لتجنب الزحام
                if node.col_offset == 0: 
                    definitions.append(f"Func: {node.name}")

        return list(imports), definitions

    def analyze_file(self, filepath):
        """تحليل ملف واحد"""
        relative_path = os.path.relpath(filepath, self.root_dir)
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # تحليل الكود
            tree = ast.parse(content)
            
            # 1. الوصف (Docstring)
            docstring = ast.get_docstring(tree)
            if not docstring:
                docstring = "No description provided."
            else:
                # اختصار الوصف إذا كان طويلاً
                docstring = docstring.strip().split('\n')[0]

            # 2. البيئة والمكونات
            imports, definitions = self.get_imports_and_defs(tree)
            
            # 3. تحديد الوظيفة التقريبية
            # إذا كان هناك وصف نستخدمه، وإلا نستخدم أسماء الكلاسات كدليل
            functionality = docstring
            if functionality == "No description provided." and definitions:
                functionality = f"Contains: {', '.join(definitions[:3])}..."

            return {
                "path": relative_path,
                "location": os.path.dirname(relative_path) or "Root",
                "functionality": functionality,
                "environment": ", ".join(sorted(imports)) if imports else "Standard Python",
                "definitions": definitions
            }

        except Exception as e:
            return {
                "path": relative_path,
                "location": os.path.dirname(relative_path),
                "functionality": f"Error parsing file: {str(e)}",
                "environment": "Unknown",
                "definitions": []
            }

    def scan(self):
        print(f"🚀 Starting scan in: {self.root_dir}")
        for root, dirs, files in os.walk(self.root_dir):
            # تنظيف المجلدات المستبعدة
            dirs[:] = [d for d in dirs if d.lower() not in self.ignore_patterns]
            
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    
                    if not self.is_test_file(full_path):
                        print(f"   -> Analyzing: {file}")
                        data = self.analyze_file(full_path)
                        self.report_data.append(data)
                        
    def generate_markdown_report(self, output_file="PROJECT_ANALYSIS_REPORT.md"):
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# 📊 AGL Project Analysis Report\n")
            f.write(f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Root Directory:** `{self.root_dir}`\n")
            f.write(f"**Total Python Files:** {len(self.report_data)}\n\n")
            
            f.write("---\n\n")
            
            # Table
            f.write("| File Path | Functionality / Description | Environment (Imports) | Location |\n")
            f.write("|-----------|----------------------------|-----------------------|----------|\n")
            
            for item in sorted(self.report_data, key=lambda x: x['path']):
                # تنظيف النصوص للجدول
                func = item['functionality'].replace('|', '-').replace('\n', ' ')
                env = item['environment'].replace('|', '-')
                path = f"`{item['path']}`"
                
                f.write(f"| {path} | {func} | {env} | {item['location']} |\n")
        
        print(f"\n✅ Report generated successfully: {output_file}")

# ==============================================================================
# EXECUTION
# ==============================================================================

if __name__ == "__main__":
    # تحديد مسار المشروع (المجلد الحالي)
    current_dir = os.getcwd()
    
    scanner = ProjectScanner(current_dir)
    scanner.scan()
    scanner.generate_markdown_report()
