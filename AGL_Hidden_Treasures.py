import os
import ast
import sys
from pathlib import Path

# Keywords indicating "Power"
POWER_KEYWORDS = [
    "Quantum", "Neural", "Engine", "Consciousness", "Heikal", 
    "Evolution", "Resonance", "Holographic", "Super", "AGI",
    "Optimization", "Genetic", "Algorithm", "Deep", "Meta"
]

def analyze_file_power(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        score = 0
        details = []
        
        # 1. Keyword Density
        for kw in POWER_KEYWORDS:
            count = content.count(kw)
            if count > 0:
                score += count * 1  # 1 point per keyword
                
        # 2. Class Complexity
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    score += 10 # 10 points per class
                    # Check methods
                    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    score += len(methods) * 2 # 2 points per method
        except:
            pass # Ignore syntax errors for scoring
            
        return score
    except:
        return 0

def find_unused_powerful_files(root_dir):
    print("🕵️‍♂️ [AGL Treasure Hunter] Scanning for hidden powerful artifacts...")
    
    all_py_files = []
    for root, dirs, files in os.walk(root_dir):
        if "venv" in root or "__pycache__" in root or ".git" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                all_py_files.append(os.path.join(root, file))
                
    print(f"   -> Found {len(all_py_files)} Python files.")
    
    # 1. Identify Imports (Usage)
    imported_modules = set()
    for file_path in all_py_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_modules.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_modules.add(node.module.split('.')[0])
        except:
            pass
            
    # 2. Score and Filter
    hidden_treasures = []
    
    for file_path in all_py_files:
        file_name = os.path.basename(file_path)
        module_name = file_name.replace(".py", "")
        
        # Skip main entry points (they are used by definition)
        if "AGL_Super_Intelligence" in file_name or "main" in file_name:
            continue
            
        # Check if likely unused (not in common imports list - simplified check)
        # This is a heuristic. A better way is to check if the file is imported by others.
        # For now, we assume if it's not in the top-level imports of the main system, it might be "dormant".
        
        power_score = analyze_file_power(file_path)
        
        if power_score > 50: # Threshold for "Powerful"
            hidden_treasures.append({
                "path": file_path,
                "score": power_score,
                "name": file_name
            })
            
    # Sort by power
    hidden_treasures.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n💎 Found {len(hidden_treasures)} Potentially Powerful Files:\n")
    
    for i, item in enumerate(hidden_treasures[:20]): # Show top 20
        print(f"{i+1}. [{item['score']}] {item['name']}")
        print(f"    Path: {item['path']}")
        
    # Save report
    with open("AGL_HIDDEN_TREASURES.md", "w", encoding="utf-8") as f:
        f.write("# 💎 AGL Hidden Treasures Report\n\n")
        f.write("Files identified as high-complexity/powerful but potentially underutilized.\n\n")
        for item in hidden_treasures:
            f.write(f"- **{item['name']}** (Score: {item['score']})\n")
            f.write(f"  - Path: `{item['path']}`\n")

if __name__ == "__main__":
    find_unused_powerful_files(os.getcwd())
