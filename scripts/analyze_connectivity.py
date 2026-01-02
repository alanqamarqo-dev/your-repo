import os
import ast
import sys
import json
from collections import defaultdict

def get_module_path(import_name, current_file_dir, root_dir):
    """
    Tries to resolve a python import to a concrete file path.
    """
    # 1. Check relative import
    parts = import_name.split('.')
    
    # Try relative to current file
    candidate = os.path.join(current_file_dir, *parts) + ".py"
    if os.path.exists(candidate): return candidate
    
    candidate_dir = os.path.join(current_file_dir, *parts, "__init__.py")
    if os.path.exists(candidate_dir): return candidate_dir
    
    # Try relative to root
    candidate = os.path.join(root_dir, *parts) + ".py"
    if os.path.exists(candidate): return candidate
    
    candidate_dir = os.path.join(root_dir, *parts, "__init__.py")
    if os.path.exists(candidate_dir): return candidate_dir
    
    return None

def analyze_imports(root_dir):
    print(f"=== SYSTEM CONNECTIVITY ANALYSIS ===")
    print(f"Root: {root_dir}")
    
    graph = defaultdict(list) # file -> list of dependencies
    reverse_graph = defaultdict(list) # file -> list of dependents
    broken_links = []
    all_files = set()
    
    # Walk through all files
    for root, dirs, files in os.walk(root_dir):
        if '__pycache__' in root or '.git' in root or 'venv' in root or 'site-packages' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir)
                all_files.add(rel_path)
                
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                        
                    for node in ast.walk(tree):
                        target = None
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                target = alias.name
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                target = node.module
                                
                        if target:
                            # Filter out standard library (heuristic)
                            if target in sys.builtin_module_names: continue
                            
                            resolved = get_module_path(target, root, root_dir)
                            
                            if resolved:
                                resolved_rel = os.path.relpath(resolved, root_dir)
                                # Ignore self-references
                                if resolved_rel != rel_path:
                                    graph[rel_path].append(resolved_rel)
                                    reverse_graph[resolved_rel].append(rel_path)
                            else:
                                # If it's not a standard lib and not found, might be broken or external pip package
                                # We only care about internal broken links mostly
                                if target.startswith('Core_Engines') or target.startswith('dynamic_modules'):
                                    broken_links.append({
                                        'source': rel_path,
                                        'target': target,
                                        'line': node.lineno
                                    })
                                    
                except Exception as e:
                    pass # Skip parse errors

    # Analysis
    orphans = []
    for f in all_files:
        if f not in reverse_graph and f != 'top_level.txt': # No one imports this
            # Check if it's a main script (entry point)
            if 'run_' not in f and 'test_' not in f and 'demo_' not in f:
                orphans.append(f)

    print(f"\n[Topology Report]")
    print(f"   Total Nodes (Files): {len(all_files)}")
    print(f"   Total Connections: {sum(len(v) for v in graph.values())}")
    
    print(f"\n🚨 BROKEN LINKS (Internal Disconnects): {len(broken_links)}")
    for link in broken_links[:10]:
        print(f"   ❌ {link['source']} (Line {link['line']}) --> Cannot find '{link['target']}'")
        
    print(f"\n🏝️ ORPHAN FILES (Disconnected Islands): {len(orphans)}")
    print("   (Files that are never imported by others - potential dead code)")
    for orphan in orphans[:10]:
        print(f"   ⚠️ {orphan}")
        
    # Central Hubs
    print(f"\nhub CENTRAL HUBS (Most Depended Upon):")
    sorted_hubs = sorted(reverse_graph.items(), key=lambda x: len(x[1]), reverse=True)
    for hub, dependents in sorted_hubs[:5]:
        print(f"   🌟 {hub}: Used by {len(dependents)} files")

if __name__ == "__main__":
    analyze_imports(os.path.join(os.getcwd(), 'repo-copy'))
