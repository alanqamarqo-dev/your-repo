import os
import ast
import sys
import numpy as np

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))
from Core_Engines.Resonance_Optimizer import ResonanceOptimizer

def analyze_file_resonance(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        
        # 1. Calculate Complexity (Barrier V)
        # Length, number of functions, number of branches
        num_lines = len(content.splitlines())
        num_functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
        num_classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        
        # Normalize complexity (0-10 scale)
        complexity = (num_lines / 500.0) + (num_functions / 10.0) + (num_classes / 2.0)
        V = min(10.0, complexity)
        
        # 2. Calculate Coherence (Energy E)
        # Docstrings, Type Hints
        has_module_doc = ast.get_docstring(tree) is not None
        num_func_docs = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and ast.get_docstring(node):
                num_func_docs += 1
                
        coherence = 0.0
        if has_module_doc: coherence += 2.0
        if num_functions > 0:
            coherence += (num_func_docs / num_functions) * 5.0
        else:
            coherence += 5.0 # No functions, so "perfectly" documented if module doc exists
            
        E = min(10.0, coherence)
        
        return V, E, num_lines
        
    except Exception as e:
        return 0, 0, 0

def find_candidate():
    root_dir = os.path.join(os.getcwd(), 'repo-copy', 'Core_Engines')
    optimizer = ResonanceOptimizer()
    
    candidates = []
    
    print(f"🔍 Scanning {root_dir} for Dissonant Files...")
    print(f"{'File':<40} | {'Barrier (V)':<10} | {'Energy (E)':<10} | {'Resonance Gap'}")
    print("-" * 80)
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                path = os.path.join(root, file)
                V, E, lines = analyze_file_resonance(path)
                
                # We want High Barrier (Complex) and Low Energy (Poorly Documented)
                # Gap = V - E. Positive Gap means "Dissonance".
                gap = V - E
                
                if lines > 100: # Ignore tiny files
                    candidates.append({
                        'file': file,
                        'path': path,
                        'V': V,
                        'E': E,
                        'gap': gap
                    })
                    if gap > 2.0:
                        print(f"{file:<40} | {V:<10.2f} | {E:<10.2f} | {gap:.2f}")

    # Sort by Gap (Descending)
    candidates.sort(key=lambda x: x['gap'], reverse=True)
    
    if candidates:
        best = candidates[0]
        print("\n🎯 [TARGET IDENTIFIED]")
        print(f"   File: {best['file']}")
        print(f"   Reason: Highest Resonance Gap ({best['gap']:.2f}).")
        print(f"   Complexity (V): {best['V']:.2f} (High Barrier)")
        print(f"   Coherence (E):  {best['E']:.2f} (Low Energy)")
        print("   Action: Apply Resonance Refactoring (Inject Docstrings + Structure).")
        return best['path']
    else:
        print("No suitable candidates found.")
        return None

if __name__ == "__main__":
    find_candidate()
