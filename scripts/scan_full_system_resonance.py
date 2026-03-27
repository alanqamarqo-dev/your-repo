import sys
import os
import ast
import time
import json
from pathlib import Path

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

try:
    from Core_Engines.Resonance_Optimizer import ResonanceOptimizer
except ImportError:
    # Fallback if not found in path
    sys.path.append(os.path.join(os.getcwd(), 'AGL', 'repo-copy'))
    from Core_Engines.Resonance_Optimizer import ResonanceOptimizer

def analyze_file_metrics(filepath):
    """
    Parses a python file and extracts functions/classes as candidates.
    Returns a list of dicts: {'id': name, 'energy': complexity, 'coherence': quality}
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
    except Exception as e:
        # Skip files that can't be parsed (e.g. syntax errors or encoding issues)
        return []

    candidates = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            name = node.name
            
            # 1. Calculate Energy (Complexity/Barrier)
            # Heuristic: Length of code + Depth of nesting
            start_line = node.lineno
            end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
            length = end_line - start_line
            
            # Normalize length: 0.0 to 1.0 (assuming max length 100 for a unit)
            energy = min(length / 100.0, 0.95)
            if energy < 0.1: energy = 0.1
            
            # 2. Calculate Coherence (Quality/Resonance)
            coherence = 0.0
            
            # Docstring?
            if ast.get_docstring(node):
                coherence += 0.4
            
            # Type hints? (Check args or returns)
            has_types = False
            if isinstance(node, ast.FunctionDef):
                if node.returns: has_types = True
                for arg in node.args.args:
                    if arg.annotation: has_types = True
            
            if has_types:
                coherence += 0.4
                
            # Naming convention (Snake case for func, Pascal for class)
            if isinstance(node, ast.FunctionDef) and name.islower():
                coherence += 0.2
            elif isinstance(node, ast.ClassDef) and name[0].isupper():
                coherence += 0.2
                
            # Cap coherence
            coherence = min(coherence, 0.99)
            if coherence < 0.01: coherence = 0.01
            
            rel_path = os.path.relpath(filepath, os.getcwd())
            
            candidates.append({
                'id': f"{rel_path}::{name}",
                'type': type(node).__name__,
                'energy': energy,       # Barrier
                'coherence': coherence, # Resonance
                'lines': length,
                'file': rel_path
            })
            
    return candidates

def run_full_system_scan():
    print("=== FULL SYSTEM RESONANCE SCAN INITIATED ===")
    print("Objective: Map the cognitive resonance of the entire AGL codebase.")
    
    root_dir = os.path.join(os.getcwd(), 'repo-copy')
    all_candidates = []
    files_scanned = 0
    
    print(f"[Scanning] Walking through {root_dir}...")
    
    for root, dirs, files in os.walk(root_dir):
        # Skip hidden folders and cache
        if '__pycache__' in root or '.git' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                candidates = analyze_file_metrics(full_path)
                all_candidates.extend(candidates)
                files_scanned += 1
                if files_scanned % 50 == 0:
                    print(f"   ...scanned {files_scanned} files ({len(all_candidates)} units found)...")

    print(f"\n[Analysis] Scan Complete.")
    print(f"   Files Processed: {files_scanned}")
    print(f"   Code Units Found: {len(all_candidates)}")
    
    # Initialize Engine
    optimizer = ResonanceOptimizer()
    
    print("\n[Action] Applying Quantum Resonance Filter to ALL units...")
    
    survivors = []
    blocked = []
    
    for cand in all_candidates:
        energy = cand['energy']
        coherence = cand['coherence']
        
        status = "Standard"
        
        # Logic: High Energy (>0.6) needs High Coherence to pass
        if energy > 0.6: 
            if coherence > energy:
                status = "Classical Passage (Masterpiece)"
                survivors.append(cand)
            else:
                # Tunneling check
                gap = energy - coherence
                if gap < 0.3: 
                    status = "TUNNELED (Complex but Valuable)"
                    cand['tunneled'] = True
                    survivors.append(cand)
                else:
                    status = "BLOCKED (Dissonant/Technical Debt)"
                    blocked.append(cand)
        else:
            # Low energy items pass easily
            survivors.append(cand)
            
        cand['status'] = status

    # Amplification
    amplified_results = optimizer.filter_solutions(survivors, target_metric=1.0)
    
    # Reporting
    print("\n" + "="*60)
    print(">>> SYSTEM RESONANCE REPORT <<<")
    print("="*60)
    
    print(f"\n📊 Overall Health:")
    print(f"   Total Units: {len(all_candidates)}")
    print(f"   Resonant Units: {len(survivors)} ({(len(survivors)/len(all_candidates))*100:.1f}%)")
    print(f"   Dissonant Units: {len(blocked)} ({(len(blocked)/len(all_candidates))*100:.1f}%)")
    
    print("\n🌟 TOP 10 MOST RESONANT COMPONENTS (The 'Genius' Core):")
    for i, res in enumerate(amplified_results[:10]):
        print(f"{i+1}. {res['id']}")
        print(f"   Score: {res['resonance_score']:.2f} | Amp: {res['amplification']:.2f}x")
        print(f"   Status: {res['status']}")
        
    if blocked:
        print("\n⚠️ TOP 10 MOST DISSONANT COMPONENTS (Critical Refactor Targets):")
        # Sort blocked by Gap (Energy - Coherence) descending
        blocked.sort(key=lambda x: x['energy'] - x['coherence'], reverse=True)
        for i, res in enumerate(blocked[:10]):
            print(f"{i+1}. {res['id']}")
            print(f"   Barrier: {res['energy']:.2f} | Coherence: {res['coherence']:.2f}")
            print(f"   Gap: {res['energy'] - res['coherence']:.2f}")
            print(f"   Lines: {res['lines']}")

    # Save report
    report = {
        "stats": {
            "total": len(all_candidates),
            "resonant": len(survivors),
            "dissonant": len(blocked)
        },
        "top_resonant": amplified_results[:20],
        "top_dissonant": blocked[:20]
    }
    
    with open('full_system_resonance_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n[Info] Full report saved to 'full_system_resonance_report.json'")

if __name__ == "__main__":
    run_full_system_scan()
