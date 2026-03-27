import sys
import importlib
import types

# [AGL] Auto-configure System Paths
try:
    from .AGL_Paths import PathManager
except ImportError:
    # Fallback if running directly from AGL_Core
    try:
        import AGL_Paths
    except ImportError:
        print("⚠️ [AGL_Unified_Python] Warning: Could not load AGL_Paths.")

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

    def _unify_category(self, category_name, lib_list):
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

    def execute_code(self, code_str, context={}):
        """Executes Python code using the Unified Library context."""
        # Inject unified namespaces into the execution context
        exec_globals = {
            'std': self.std,
            'sci': self.sci,
            'ai': self.ai,
            'net': self.net,
            'np': self.sci.numpy, # Shortcut
            'pd': self.sci.pandas, # Shortcut
        }
        # Add matplotlib.pyplot if available
        if self.sci.matplotlib:
            try:
                import matplotlib.pyplot as plt
                exec_globals['plt'] = plt
            except ImportError:
                pass
                
        exec_globals.update(context)
        
        try:
            exec(code_str, exec_globals)
            return exec_globals
        except Exception as e:
            return f"❌ Execution Error: {e}"

# Singleton
UnifiedLib = AGL_Unified_Python()


def evolved_capability_1767044807():
    '''Auto-generated evolution'''
    return 'I have evolved at Tue Dec 30 00:46:47 2025'
