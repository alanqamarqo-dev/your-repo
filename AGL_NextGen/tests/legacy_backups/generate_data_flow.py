import os
import ast
import json

def get_imports(file_path, root_pkg_path):
    with open(file_path, "r", encoding="utf-8") as source:
        try:
            tree = ast.parse(source.read())
        except:
            return []

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
            elif node.level > 0:
                # Handle relative imports (simplified)
                # This is tricky without knowing the exact package structure relative to the file
                # For this visualization, we might skip deep relative resolution or try a best guess
                pass
    
    # Filter for project-internal imports only (starting with 'agl')
    internal_imports = {imp for imp in imports if imp.startswith('agl') or imp.startswith('Core_Engines') or imp.startswith('AGL_')}
    return list(internal_imports)

def build_dependency_graph(start_path):
    graph = {}
    file_map = {} # Maps full path to module name

    # 1. Map all files to their likely module names
    for root, dirs, files in os.walk(start_path):
        if 'node_modules' in root or '__pycache__' in root or 'backups' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                full_path = os.path.join(root, f)
                # Create a relative module name like agl.core.super_intelligence
                rel_path = os.path.relpath(full_path, os.path.dirname(start_path))
                module_name = rel_path.replace(os.sep, '.').replace('.py', '')
                file_map[full_path] = module_name
                graph[module_name] = []

    # 2. Analyze imports for each file
    for full_path, module_name in file_map.items():
        imports = get_imports(full_path, start_path)
        graph[module_name] = imports

    return graph

def generate_mermaid_flowchart(graph):
    # Start Mermaid definition
    lines = ["graph TD;"]
    
    # Clean up the graph to remove disconnected nodes or external libs if desired
    # For now, we keep only edges where both source and target are "known" in our scanned graph
    # or at least look like project files.
    
    known_modules = set(graph.keys())
    
    # We want to focus on high-level data flow, so maybe group by subfolders?
    # Let's just do a direct file-to-file map first.
    
    edges_count = 0
    
    for source, targets in graph.items():
        # Simplify source name for display (e.g. agl.core.super_intelligence -> super_intelligence)
        source_short = source.split('.')[-1]
        
        if source_short == "__init__": continue

        for target in targets:
            # Check if target is in our project
            # This logic mimics whether 'target' starts with 'agl' mostly
            
            # Draw edge
            # We try to match the import to a known module
            # e.g. import agl.engines.optical_heart -> matches agl.engines.optical_heart
            
            matched_target = None
            if target in known_modules:
                matched_target = target
            else:
                # Try partial match (e.g. importing a class from a module)
                # If target is agl.engines.optical_heart.OpticalHeart, we match agl.engines.optical_heart
                parts = target.split('.')
                while parts:
                    sub = '.'.join(parts)
                    if sub in known_modules:
                        matched_target = sub
                        break
                    parts.pop()
            
            if matched_target and matched_target != source:
                target_short = matched_target.split('.')[-1]
                if target_short == "__init__": continue
                
                # Add edge to mermaid
                # Using cleaned names to avoid syntax errors
                s_safe = source_short.replace('-', '_').replace(' ', '_')
                t_safe = target_short.replace('-', '_').replace(' ', '_')
                
                # Label edge if possible (optional)
                lines.append(f"    {s_safe} --> {t_safe};")
                edges_count += 1

    return "\n".join(lines)

def print_text_graph(graph):
    print("\n🔗 Data Flow & Dependencies (Most Critical):")
    
    # Filter for 'Core' or 'Main' related files to keep it readable
    priority_nodes = [k for k in graph.keys() if 'core' in k.lower() or 'main' in k.lower() or 'engine' in k.lower()]
    
    for node in sorted(priority_nodes):
        deps = graph[node]
        if not deps: continue
        
        # Clean deps
        clean_deps = []
        for d in deps:
            if d.startswith('agl'):
                clean_deps.append(d.split('.')[-1])
        
        if clean_deps:
            short_name = node.split('.')[-1]
            print(f"  🔹 [{short_name}] يعتمد على (Inputs from):")
            for d in sorted(clean_deps):
                print(f"      ---> {d}")
            print("")

if __name__ == "__main__":
    src_path = os.path.join("D:\\AGL\\AGL_NextGen\\src\\agl")
    graph = build_dependency_graph(src_path)
    
    print_text_graph(graph)
    
    print("\n🎨 Mermaid Diagram Code (To visualize flow):")
    diagram = generate_mermaid_flowchart(graph)
    print(diagram)
