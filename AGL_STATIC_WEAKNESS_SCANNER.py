import os
import re
import ast
import sys
import time

class AGLStaticScanner:
    def __init__(self, root_dir):
        self.root_dir = os.path.abspath(root_dir)
        self.system_map_path = os.path.join(self.root_dir, "AGL_SYSTEM_MAP.md")
        self.entry_point = os.path.join(self.root_dir, "AGL_Core", "AGL_Awakened.py")
        self.all_files = set()
        self.active_files = set()
        self.scanned_files = set()

    def parse_system_map(self):
        print(f"🗺️ Reading System Map from: {self.system_map_path}")
        if not os.path.exists(self.system_map_path):
            print("❌ System Map not found!")
            return

        with open(self.system_map_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex to find file paths: - **Path/To/File.py**
        matches = re.findall(r'- \*\*(.*?)\*\*', content)
        for match in matches:
            # Normalize path
            full_path = os.path.join(self.root_dir, match.replace('/', os.sep).replace('\\', os.sep))
            self.all_files.add(full_path)
        
        print(f"✅ Found {len(self.all_files)} files in System Map.")

    def get_imports(self, file_path):
        imports = set()
        if not os.path.exists(file_path):
            return imports

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=file_path)
        except Exception as e:
            # print(f"⚠️ Could not parse {file_path}: {e}")
            return imports

        file_dir = os.path.dirname(file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(self.resolve_import(alias.name, file_dir))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # from module import ...
                    imports.add(self.resolve_import(node.module, file_dir, level=node.level))
                else:
                    # from . import ...
                    imports.add(self.resolve_import('.', file_dir, level=node.level))
        
        return {i for i in imports if i} # Filter None

    def resolve_import(self, module_name, current_dir, level=0):
        # Handle relative imports
        if level > 0:
            # Go up levels
            base = current_dir
            for _ in range(level - 1):
                base = os.path.dirname(base)
            
            if module_name == '.':
                # Just the directory
                target = base
            else:
                parts = module_name.split('.')
                target = os.path.join(base, *parts)
        else:
            # Absolute import (relative to root or python path)
            # We assume root_dir is in python path
            parts = module_name.split('.')
            target = os.path.join(self.root_dir, *parts)

        # Check if it's a file or directory
        py_file = target + ".py"
        if os.path.exists(py_file):
            return py_file
        
        init_file = os.path.join(target, "__init__.py")
        if os.path.exists(init_file):
            return init_file
            
        return None

    def scan_dependencies(self, file_path):
        if file_path in self.scanned_files:
            return
        
        self.scanned_files.add(file_path)
        self.active_files.add(file_path)
        
        # print(f"Scanning: {os.path.basename(file_path)}")
        
        imports = self.get_imports(file_path)
        for imp in imports:
            self.scan_dependencies(imp)

    def run(self):
        self.parse_system_map()
        
        print(f"🚀 Tracing dependencies starting from: {os.path.basename(self.entry_point)}")
        self.scan_dependencies(self.entry_point)
        
        print(f"✅ Trace complete. Found {len(self.active_files)} active files.")
        
        # Calculate Weaknesses
        orphaned = self.all_files - self.active_files
        
        # Filter out non-existent files (maybe map is outdated)
        real_orphans = [f for f in orphaned if os.path.exists(f)]
        
        print(f"⚠️ Found {len(real_orphans)} Disconnected Components (Orphans).")
        
        # Categorize
        tests = []
        docs = []
        backups = []
        core_logic = []
        
        for f in real_orphans:
            name = os.path.basename(f).lower()
            if "test" in name or "demo" in name:
                tests.append(f)
            elif "report" in name or "doc" in name or ".md" in f: # .md won't be in all_files usually but just in case
                docs.append(f)
            elif "backup" in name or "old" in name or "legacy" in name:
                backups.append(f)
            else:
                core_logic.append(f)
        
        report = "# 🕵️‍♂️ AGL ARCHITECTURAL WEAKNESS REPORT (STATIC ANALYSIS)\n\n"
        report += f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Total Files in Map:** {len(self.all_files)}\n"
        report += f"**Active Files (Linked to Core):** {len(self.active_files)}\n"
        report += f"**Disconnected Components:** {len(real_orphans)}\n\n"
        
        report += "## 🔴 CRITICAL WEAKNESSES (Disconnected Core Logic)\n"
        report += "These modules exist but are not reachable from `AGL_Awakened.py`:\n\n"
        for f in sorted(core_logic):
            rel = os.path.relpath(f, self.root_dir)
            report += f"- `{rel}`\n"
            
        report += "\n## 🟡 DORMANT TESTS & DEMOS\n"
        for f in sorted(tests):
            rel = os.path.relpath(f, self.root_dir)
            report += f"- `{rel}`\n"

        report += "\n## ⚪ BACKUPS & LEGACY\n"
        for f in sorted(backups):
            rel = os.path.relpath(f, self.root_dir)
            report += f"- `{rel}`\n"
            
        with open("AGL_WEAKNESS_REPORT_STATIC.md", "w", encoding="utf-8") as f:
            f.write(report)
            
        print("\n📄 Report generated: AGL_WEAKNESS_REPORT_STATIC.md")
        print(report)

if __name__ == "__main__":
    scanner = AGLStaticScanner(os.path.dirname(os.path.abspath(__file__)))
    scanner.run()
