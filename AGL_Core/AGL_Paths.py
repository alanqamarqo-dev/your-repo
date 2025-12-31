import sys
import os

class AGL_Path_Manager:
    """
    🗺️ AGL Path Manager
    Centralizes path configuration for the entire AGL system.
    Ensures all modules (Core, Repo-Copy, etc.) are importable from anywhere.
    """
    def __init__(self):
        self.root_dir = self._find_root()
        self.repo_copy_dir = os.path.join(self.root_dir, "repo-copy")
        self.core_dir = os.path.join(self.root_dir, "AGL_Core")
        
        self._setup_paths()

    def _find_root(self):
        """
        Locates the project root (d:\AGL) by looking for specific markers.
        """
        current = os.path.abspath(os.path.dirname(__file__))
        
        # Traverse up until we find 'repo-copy' or hit root
        while True:
            if os.path.exists(os.path.join(current, "repo-copy")):
                return current
            
            parent = os.path.dirname(current)
            if parent == current: # Hit filesystem root
                # Fallback to hardcoded if we are lost, or current dir
                return os.getcwd() 
            current = parent

    def _setup_paths(self):
        """
        Adds critical directories to sys.path if missing.
        """
        paths_to_add = [
            self.root_dir,
            self.repo_copy_dir,
            self.core_dir,
            # Add sub-modules if needed
            os.path.join(self.repo_copy_dir, "Core_Engines"),
            os.path.join(self.repo_copy_dir, "Integration_Layer"),
            os.path.join(self.repo_copy_dir, "Safety_Systems"),

            # Add .venv site-packages (Fix for missing libraries)
            os.path.join(self.root_dir, ".venv", "Lib", "site-packages"),
        ]

        count = 0
        for p in paths_to_add:
            if p not in sys.path:
                sys.path.insert(0, p) # Insert at start to prioritize local modules
                count += 1
        
        if count > 0:
            print(f"🗺️ [AGL_Paths] Unified {count} system paths.")

# Singleton Instance
PathManager = AGL_Path_Manager()
