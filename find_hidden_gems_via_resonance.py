import os
import sys
import ast
import math

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

class QuantumResonanceScanner:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.integrated_modules = self._get_integrated_modules()
        self.power_keywords = {
            "Quantum": 10, "Neural": 8, "Meta": 9, "Consciousness": 10,
            "Reasoning": 7, "Graph": 6, "Evolution": 8, "Self": 7,
            "Dynamic": 6, "Holographic": 10, "Resonance": 9, "Hyper": 8,
            "Omni": 9, "Unified": 8, "Genesis": 10, "Dreaming": 7
        }

    def _get_integrated_modules(self):
        """Extracts modules already imported in Heikal_Quantum_Core.py"""
        core_path = os.path.join(self.root_dir, "Core_Engines", "Heikal_Quantum_Core.py")
        integrated = set()
        
        if not os.path.exists(core_path):
            return integrated

        with open(core_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    # Extract the last part of the module path (e.g., 'Core_Engines.Self_Reflective' -> 'Self_Reflective')
                    module_name = node.module.split('.')[-1]
                    integrated.add(module_name)
                    # Also add the class names imported
                    for name in node.names:
                        integrated.add(name.name)
                        
        return integrated

    def calculate_resonance(self, file_path, content):
        """Calculates the 'Resonance Score' of a file based on its content."""
        score = 0.0
        
        # 1. Keyword Resonance
        for keyword, weight in self.power_keywords.items():
            count = content.count(keyword)
            if count > 0:
                # Logarithmic scaling to prevent spamming keywords from dominating
                score += weight * (1 + math.log(count))

        # 2. Structural Complexity (Classes & Functions)
        try:
            tree = ast.parse(content)
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            
            score += len(classes) * 5
            score += len(functions) * 1
        except:
            pass # Ignore parsing errors

        # 3. Size Factor (Too small = insignificant, Too big = messy)
        lines = len(content.splitlines())
        if 50 < lines < 1000:
            score += 10
            
        return score

    def scan(self):
        print("\n📡 [QSR Scanner]: Initiating Quantum Synaptic Resonance Scan...")
        print(f"   Target: {self.root_dir}")
        print(f"   Excluding (Already Integrated): {len(self.integrated_modules)} modules")
        print("-" * 60)
        
        candidates = []

        for root, _, files in os.walk(self.root_dir):
            # Exclude virtual environments and libraries
            if ".venv" in root or "site-packages" in root or "__pycache__" in root:
                continue

            for file in files:
                if not file.endswith(".py"):
                    continue
                    
                # Skip tests, backups, and the core itself
                if "test" in file.lower() or "backup" in root.lower() or "Heikal_Quantum_Core" in file:
                    continue
                
                module_name = file.replace(".py", "")
                
                # Skip if already integrated
                if module_name in self.integrated_modules:
                    continue

                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    score = self.calculate_resonance(file_path, content)
                    
                    if score > 20: # Minimum resonance threshold
                        candidates.append({
                            "name": module_name,
                            "path": os.path.relpath(file_path, self.root_dir),
                            "score": score
                        })
                except Exception as e:
                    pass

        # Sort by Resonance Score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        print(f"✨ Found {len(candidates)} dormant artifacts with high resonance.\n")
        
        print(f"{'Resonance':<10} | {'Module Name':<30} | {'Path':<40}")
        print("-" * 85)
        
        for c in candidates[:15]: # Show top 15
            print(f"⚡ {c['score']:<8.1f} | {c['name']:<30} | {c['path']:<40}")
            
        print("-" * 85)
        return candidates

if __name__ == "__main__":
    scanner = QuantumResonanceScanner(os.path.join(os.getcwd(), "repo-copy"))
    scanner.scan()
