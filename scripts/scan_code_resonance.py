import sys
import os
import ast
import time
import json

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Resonance_Optimizer import ResonanceOptimizer

def analyze_file_metrics(filepath):
    """
    Parses a python file and extracts functions/classes as candidates.
    Returns a list of dicts: {'id': name, 'energy': complexity, 'coherence': quality}
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    tree = ast.parse(source)
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
            
            candidates.append({
                'id': f"{os.path.basename(filepath)}::{name}",
                'type': type(node).__name__,
                'energy': energy,       # Barrier
                'coherence': coherence, # Resonance
                'lines': length
            })
            
    return candidates

def run_code_resonance_scan():
    print("=== System Self-Scan: Code Resonance Analysis ===")
    print("Objective: Identify 'Resonant' (High Value) and 'Dissonant' (High Risk) components.")
    
    # Scan all of repo-copy
    scan_root = os.path.join(os.getcwd(), 'repo-copy')
    all_candidates = []
    
    print(f"\n[Scanning] Root: {scan_root}")
    
    for root, dirs, files in os.walk(scan_root):
        if "__pycache__" in root or ".git" in root or "node_modules" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                # print(f"   Scanning {file}...") # Too verbose for full scan
                try:
                    candidates = analyze_file_metrics(full_path)
                    all_candidates.extend(candidates)
                except Exception as e:
                    print(f"   [Error] Failed to scan {file}: {e}")

    print(f"\n[Analysis] Total Units to Process: {len(all_candidates)}")
    
    # Initialize Engine
    optimizer = ResonanceOptimizer()
    
    # Run the Optimizer Logic manually to get detailed stats
    # We want to see what tunnels and what gets amplified
    
    print("\n[Action] Applying Quantum Resonance Filter...")
    
    # 1. Tunneling Phase (Filter out High Energy + Low Coherence)
    survivors = []
    blocked = []
    
    for cand in all_candidates:
        # Use the engine's internal logic if possible, or replicate it for the report
        # We'll replicate the logic from process_task to show the "Tunneling" effect explicitly
        
        energy = cand['energy']
        coherence = cand['coherence']
        
        tunneled = False
        status = "Standard"
        
        if energy > 0.6: # High Barrier
            if coherence > energy:
                status = "Classical Passage (High Skill)"
                survivors.append(cand)
            else:
                # Tunneling check
                gap = energy - coherence
                # If gap is small, prob is higher. 
                # For this scan, we want to highlight "Potential Genius" vs "Technical Debt"
                if gap < 0.3: 
                    status = "TUNNELED (Complex but Valuable)"
                    cand['tunneled'] = True
                    survivors.append(cand)
                else:
                    status = "BLOCKED (Too Complex/Unclear)"
                    blocked.append(cand)
        else:
            survivors.append(cand)
            
        cand['status'] = status

    # 2. Amplification Phase (Rank survivors)
    # We use the engine's filter_solutions to calculate resonance scores
    amplified_results = optimizer.filter_solutions(survivors, target_metric=1.0)
    
    print(f"\n[Results] Scan Complete.")
    print(f"   Survivors: {len(survivors)}")
    print(f"   Blocked (Dissonant): {len(blocked)}")
    
    print("\n>>> TOP 5 RESONANT COMPONENTS (The 'Genius' Code) <<<")
    for i, res in enumerate(amplified_results[:5]):
        print(f"{i+1}. {res['id']}")
        print(f"   Type: {res['type']}, Lines: {res['lines']}")
        print(f"   Resonance Score: {res['resonance_score']:.2f} (Amp: {res['amplification']:.2f}x)")
        print(f"   Status: {res['status']}")
        print("-" * 40)
        
    if blocked:
        print("\n>>> TOP DISSONANT COMPONENTS (Refactor Candidates) <<<")
        # Sort blocked by energy (highest complexity first)
        blocked.sort(key=lambda x: x['energy'], reverse=True)
        for i, res in enumerate(blocked[:5]):
            print(f"{i+1}. {res['id']}")
            print(f"   Type: {res['type']}, Lines: {res['lines']}")
            print(f"   Barrier: {res['energy']:.2f}, Coherence: {res['coherence']:.2f}")
            print(f"   Gap: {res['energy'] - res['coherence']:.2f}")
            print("-" * 40)
    else:
        print("\n[Info] No significant dissonance found. System is highly coherent.")

if __name__ == "__main__":
    run_code_resonance_scan()
