import sys
import os

# Add repo root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from Safety_Systems.Core_Values_Lock import CoreValuesLock
except ImportError:
    # Fallback if running from different context
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'repo-copy'))
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