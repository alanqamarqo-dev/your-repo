import re
import os

class SolidityContextAggregator:
    """
    [AGL-HEIKAL] Cross-Contract Context Extractor.
    Resolves imports and extracts 'modifiers', 'requires', and 'structs' 
    to give the AI a full picture of the inheritance tree.
    """
    def __init__(self):
        self.context_cache = {}
        self.extracted_protections = []

    def scan_imports(self, file_path, depth=0, max_depth=3):
        """Recursively finds imports and extracts definitions."""
        if depth > max_depth or file_path in self.context_cache:
            return
        
        self.context_cache[file_path] = True
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Regex Find Imports
            # Pattern: import "./SingleAdminAccessControl.sol";
            imports = re.findall(r'import\s+["\'](\.?\./[^"\']+)["\'];', content)
            
            base_dir = os.path.dirname(file_path)
            
            for imp in imports:
                # Resolve Path
                resolved_path = os.path.normpath(os.path.join(base_dir, imp))
                if os.path.exists(resolved_path):
                    # Recursive Call
                    self.scan_imports(resolved_path, depth + 1, max_depth)
                    
            # 2. Extract Context (Modifiers/Structs/Events) from THIS file
            # Simple heuristic: grab modifier definitions
            modifiers = re.findall(r'modifier\s+(\w+)\s*\(([^)]*)\)\s*\{([^}]+)\}', content, re.DOTALL)
            for mod_name, args, body in modifiers:
                self.extracted_protections.append(
                    f"MODIFIER DEFINITION ({os.path.basename(file_path)}): modifier {mod_name}({args}) {{ {body[:200].strip()}... }}"
                )
                
            # Extract important state variables (heuristic)
            state_vars = re.findall(r'(mapping\s*\([^;]+\)\s*\w+\s*\w+;)', content)
            for var in state_vars[:5]: # Limit noise
                 self.extracted_protections.append(f"STATE VAR ({os.path.basename(file_path)}): {var}")

        except Exception as e:
            pass # Fail silently on file read errors to keep engine running
            
    def format_context(self):
        if not self.extracted_protections:
            return "No external context found."
        
        return "\n".join(self.extracted_protections)
