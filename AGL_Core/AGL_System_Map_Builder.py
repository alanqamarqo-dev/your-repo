import os
import ast
from pathlib import Path
import json

class AGL_System_Map_Builder:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.ignore_dirs = {
            '.git', '__pycache__', 'venv', '.venv', 'env', 'node_modules', 'artifacts', 'backups', 'dist', 'build', 
            'ل', 'لا', 'venv_cv2', 'repo-copy-HILT-experiment', 'repo-copy_test_run.info', 'htmlcov', 'htmlcov_after_retriever_fix',
            '.venvا', '.venv_embed', 'site-packages'
        }
        self.system_map = {}

    def analyze_file(self, file_path):
        """Parses a file and returns its structure (Classes/Funcs only)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
            functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
            
            return {
                "classes": classes,
                "functions": functions
            }
        except Exception as e:
            return None

    def build_map(self):
        """Walks the directory and builds the map."""
        print("🗺️  Building AGL System Map...")
        
        system_structure = {}

        for root, dirs, files in os.walk(self.root_dir):
            # Filter ignored dirs
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    # Filter temporary and hidden files
                    if file.startswith('.') or file.startswith('tmp_') or file.startswith('temp_'):
                        continue
                    if file.startswith('_') and file != '__init__.py':
                        continue

                    file_path = Path(root) / file
                    rel_path = str(file_path.relative_to(self.root_dir)).replace('\\', '/')
                    
                    structure = self.analyze_file(file_path)
                    if structure and (structure['classes'] or structure['functions']):
                        system_structure[rel_path] = structure

        # Save as JSON for machine reading
        json_path = self.root_dir / "AGL_SYSTEM_MAP.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(system_structure, f, indent=2)
            
        # Save as Concise Markdown for LLM Context
        md_path = self.root_dir / "AGL_SYSTEM_MAP.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# 🗺️ AGL System Map (Concise)\n\n")
            for path, content in sorted(system_structure.items()):
                f.write(f"- **{path}**\n")
                if content['classes']:
                    f.write(f"  - Classes: {', '.join(content['classes'])}\n")
                if content['functions']:
                    f.write(f"  - Funcs: {', '.join(content['functions'])}\n")
        
        print(f"✅ System Map (JSON) generated at: {json_path}")
        print(f"✅ System Map (MD) generated at: {md_path}")

if __name__ == "__main__":
    root = Path(r"d:\AGL")
    builder = AGL_System_Map_Builder(root)
    builder.build_map()
