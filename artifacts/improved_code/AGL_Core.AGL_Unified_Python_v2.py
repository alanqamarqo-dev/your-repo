import sys
import importlib
import types

class AGL_Unified_Python:
    """
    📚 AGL Unified Python Interface
    Centralizes access to all Python capabilities (Standard, Scientific, AI).
    Allows the AGL System to dynamically load and utilize any installed library.
    """

    def __init__(self):
        print("\n📚 [AGL_Unified_Python] Initializing Grand Library Unification...")
        self.registry = {}
        
        # 1. Standard Core
        self.std = self._unify_category("Standard", [
            'os', 'sys', 'time', 'json', 'math', 'random', 're', 'shutil', 'subprocess', 'threading', 'asyncio'
        ])
        
        # 2. Scientific Core
        self.sci = self._unify_category("Scientific", [
            'numpy', 'scipy', 'sympy', 'pandas', 'matplotlib', 'networkx'
        ])
        
        # 3. AI & ML Core
        self.ai = self._unify_category("AI/ML", [
            'torch', 'tensorflow', 'sklearn', 'transformers', 'cv2'
        ])
        
        # 4. Web & Net
        self.net = self._unify_category("Network", [
            'requests', 'urllib', 'socket', 'flask', 'fastapi'
        ])

    def _unify_category(self, category_name: str, lib_list: list) -> types.SimpleNamespace:
        """Dynamically imports a list of libraries and returns a namespace object."""
        container = types.SimpleNamespace()
        count = 0
        for lib_name in lib_list:
            try:
                module = importlib.import_module(lib_name)
                setattr(container, lib_name, module)
                self.registry[lib_name] = "Active"
                count += 1
            except ImportError:
                self.registry[lib_name] = "Missing"
                setattr(container, lib_name, None)
        
        print(f"   -> Unified {category_name}: {count}/{len(lib_list)} libraries active.")
        return container

    def execute_code(self, code_str: str, context: dict) -> Union[str, types.SimpleNamespace]:
        """Executes Python code using the Unified Library context."""
        # Inject unified namespaces into the execution context
        exec_globals = {
            'std': self.std,
            'sci': self.sci,
            'ai': self.ai,
            'net': self.net,
            'np': getattr(self.sci, 'numpy', None),  # Shortcut for numpy if available
            'pd': getattr(self.sci, 'pandas', None)   # Shortcut for pandas if available
        }
        
        # Add matplotlib.pyplot if available and not already in context
        if self.sci.matplotlib:
            try:
                import matplotlib.pyplot as plt
                exec_globals['plt'] = plt
            except ImportError:
                pass
                
        exec_globals.update(context)
        
        try:
            result = {}
            exec(code_str, exec_globals, result)
            return result
        except Exception as e:
            return f"❌ Execution Error: {e}"

# Singleton
UnifiedLib = AGL_Unified_Python()