import sys
import os

class PathManager:
    """
    🗺️ AGL Path Manager (NextGen)
    Centralizes path configuration for the AGL NextGen system.
    Ensures 'src' and other critical paths are in sys.path.
    """
    def __init__(self):
        self.root_dir = self._find_root()
        self.src_dir = os.path.join(self.root_dir, "src")
        self._setup_paths()

    def _find_root(self):
        """
        Locates the project root (AGL_NextGen) by looking for 'src' folder.
        """
        current = os.path.abspath(os.path.dirname(__file__))
        while True:
            if os.path.exists(os.path.join(current, "src")):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                # Fallback: assume we are in src/agl/lib, so root is 3 levels up
                # d:\AGL\AGL_NextGen\src\agl\lib -> d:\AGL\AGL_NextGen
                return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            current = parent

    def _setup_paths(self):
        """
        Adds critical directories to sys.path if missing.
        """
        if self.src_dir not in sys.path:
            sys.path.insert(0, self.src_dir)
            print(f"✅ [AGL_Paths] Added {self.src_dir} to sys.path")

# Auto-initialize on import to ensure paths are set
try:
    _manager = PathManager()
except Exception as e:
    print(f"⚠️ [AGL_Paths] Failed to initialize paths: {e}")
