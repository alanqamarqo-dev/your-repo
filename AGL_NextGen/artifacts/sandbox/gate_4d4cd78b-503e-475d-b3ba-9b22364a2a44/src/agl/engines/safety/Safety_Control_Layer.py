import os
import sys


def _ensure_repo_copy_on_path() -> None:
    # This file lives under: AGL_NextGen/src/agl/engines/safety
    # The repo-copy folder is typically at: <AGL>/repo-copy
    here = os.path.abspath(__file__)
    agl_nextgen_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here)))))
    agl_root = os.path.dirname(agl_nextgen_root)
    repo_copy = os.path.join(agl_root, "repo-copy")
    if os.path.isdir(repo_copy) and repo_copy not in sys.path:
        sys.path.insert(0, repo_copy)


try:
    from Safety_Systems.Core_Values_Lock import CoreValuesLock
except Exception:
    _ensure_repo_copy_on_path()
    from Safety_Systems.Core_Values_Lock import CoreValuesLock

class SafetyControlLayer:
    def __init__(self):
        self.lock = CoreValuesLock()

    def evaluate(self, improvement: dict) -> dict:
        """
        Evaluates a proposed improvement against safety protocols.
        Expected improvement dict format:
        {
            "type": "code_change",
            "file": "filename.py",
            "content": "new code content",
            ...
        }
        """
        # 1. Check if file is locked
        target_file = improvement.get("file", "")
        if self.lock.is_file_locked(target_file):
            return {
                "approved": False, 
                "reason": f"Security Violation: Attempt to modify locked file '{target_file}'."
            }

        # 2. Check content against banned keywords
        content = improvement.get("content", "")
        validation = self.lock.validate_code_change(content)
        if not validation["approved"]:
            return validation

        # 3. General Approval
        return {"approved": True, "reason": "Passed Core Values check."}

class ControlLayers:
    def __init__(self):
        self.safety_layer = SafetyControlLayer()
    
    def evaluate_improvement_safety(self, improvement):
        """تقييم أمان التحسينات"""
        return self.safety_layer.evaluate(improvement)