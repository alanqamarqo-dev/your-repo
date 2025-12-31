import sys
import os
import ast
import json
import time
import argparse
from pathlib import Path

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))
sys.path.append(os.path.join(os.getcwd(), 'AGL_Core'))

from Core_Engines.Recursive_Improver import RecursiveImprover
from AGL_System_Map_Builder import AGL_System_Map_Builder

class AGL_System_Doctor:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.improver = RecursiveImprover()
        self.map_builder = AGL_System_Map_Builder(root_dir)
        self.issues_found = []

    def explore_and_diagnose(self):
        print("🗺️ [Doctor] Initiating System Exploration & Diagnosis...")
        
        # 1. Build/Refresh Map
        self.map_builder.build_map()
        map_path = self.root_dir / "AGL_SYSTEM_MAP.json"
        
        if not map_path.exists():
            print("❌ [Doctor] Failed to generate system map.")
            return

        with open(map_path, 'r', encoding='utf-8') as f:
            system_map = json.load(f)

        print(f"   📍 Map loaded. Analyzing {len(system_map)} components...")

        # 2. Scan for Issues
        for rel_path, structure in system_map.items():
            full_path = self.root_dir / rel_path
            self._check_file_health(full_path)

        # Also scan files NOT in the map (because they might be broken and skipped by the builder)
        self._scan_unmapped_files(system_map)

        print(f"\n🩺 [Doctor] Diagnosis Complete. Found {len(self.issues_found)} issues.")

    def _scan_unmapped_files(self, system_map):
        """Finds python files that are not in the map (likely due to errors)."""
        print("   🔍 Scanning for unmapped/broken files...")
        for root, dirs, files in os.walk(self.root_dir):
            # Skip ignored dirs
            dirs[:] = [d for d in dirs if d not in self.map_builder.ignore_dirs]
            
            for file in files:
                if file.endswith(".py"):
                    full_path = Path(root) / file
                    rel_path = str(full_path.relative_to(self.root_dir)).replace('\\', '/')
                    
                    if rel_path not in system_map:
                        # This file was missed by the map builder, likely broken
                        self._check_file_health(full_path, force_check=True)

    def _check_file_health(self, file_path, force_check=False):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check 1: Syntax Error
            try:
                ast.parse(content)
            except SyntaxError as e:
                print(f"   ❌ [Syntax Error] Found in {file_path.name}: {e}")
                self.issues_found.append({
                    "file": file_path,
                    "type": "syntax_error",
                    "details": str(e)
                })
                return # Stop checking this file

            # Check 2: Empty/Stub Files (Logic Gap)
            if len(content.strip()) < 50 and "pass" in content:
                 print(f"   ⚠️ [Stub Detected] {file_path.name} seems empty/incomplete.")
                 self.issues_found.append({
                    "file": file_path,
                    "type": "stub",
                    "details": "File is too short and contains 'pass'."
                })

        except Exception as e:
            print(f"   ⚠️ [Read Error] Could not read {file_path.name}: {e}")

    def start_repairs(self):
        if not self.issues_found:
            print("✅ [Doctor] System is healthy. No repairs needed.")
            return

        print(f"\n🛠️ [Doctor] Starting Repair Sequence for {len(self.issues_found)} issues...")
        
        for issue in self.issues_found:
            target_file = issue['file']
            issue_type = issue['type']
            details = issue['details']
            
            print(f"\n   🚑 Repairing: {target_file.name} ({issue_type})")
            
            goal = ""
            if issue_type == "syntax_error":
                goal = f"Fix the Python Syntax Error in this file. Error details: {details}"
            elif issue_type == "stub":
                goal = "Implement a basic functional skeleton for this class/module based on its name. Replace 'pass' with working logic or meaningful docstrings."
            
            # Call the Engineer (Recursive Improver)
            # Note: We use apply_changes=True because we have the 'High Resonance' permission now.
            
            # Try to read the file content directly first
            try:
                with open(target_file, 'r', encoding='utf-8-sig') as f: # Handle BOM
                    code_content = f.read()
                
                print(f"      🧬 Improving arbitrary code in {target_file.name}...")
                improved_code = self.improver.improve_arbitrary_code(code_content, goal)
                
                if improved_code and not improved_code.startswith("# Evolution Failed"):
                    # Save the fix
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write(improved_code)
                    print(f"      ✅ Fixed! (Direct Write)")
                else:
                    print(f"      ❌ Failed to generate fix.")

            except Exception as e:
                print(f"      ❌ Error during repair: {e}")

    def start_enhancements(self, mode="docstrings", target_file=None):
        print(f"\n✨ [Doctor] Starting Enhancement Sequence: {mode.upper()}...")
        
        files_to_process = []
        
        if target_file:
            files_to_process.append(self.root_dir / target_file)
        else:
            # Load map
            map_path = self.root_dir / "AGL_SYSTEM_MAP.json"
            if not map_path.exists():
                self.map_builder.build_map()
            
            with open(map_path, 'r', encoding='utf-8') as f:
                system_map = json.load(f)
                
            for rel_path in system_map:
                files_to_process.append(self.root_dir / rel_path)

        count = 0
        for full_path in files_to_process:
            if not full_path.exists(): continue
            
            should_process = False
            if mode == "docstrings":
                if self._needs_docstrings(full_path):
                    should_process = True
            elif mode == "refactor":
                if target_file:
                    should_process = True
            
            if should_process:
                goal = ""
                if mode == "docstrings":
                    goal = "Add comprehensive docstrings to all classes and methods following Google style guide. Keep existing logic exactly the same."
                elif mode == "refactor":
                    goal = "Refactor code for better readability, modularity, and PEP8 compliance. Ensure no logic is broken."
                
                self._apply_enhancement(full_path, goal)
                count += 1
        
        print(f"\n✨ [Doctor] Enhancement Complete. Processed {count} files.")

    def _needs_docstrings(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        return True
            return False
        except:
            return False

    def _apply_enhancement(self, file_path, goal):
        print(f"   ✨ Enhancing {file_path.name}...")
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            improved = self.improver.improve_arbitrary_code(content, goal)
            
            if improved and not improved.startswith("# Evolution Failed"):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(improved)
                print(f"      ✅ Enhanced!")
            else:
                print(f"      ❌ Failed to enhance.")
        except Exception as e:
            print(f"      ❌ Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--enhance", choices=["docstrings", "refactor"], help="Run enhancement mode")
    parser.add_argument("--target", help="Specific file to enhance (relative path)")
    args = parser.parse_args()

    doctor = AGL_System_Doctor(os.getcwd())
    
    if args.enhance:
        doctor.start_enhancements(mode=args.enhance, target_file=args.target)
    else:
        doctor.explore_and_diagnose()
        doctor.start_repairs()
