import sys
import os
from typing import Dict, Any

# Ensure paths
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'repo-copy'))

try:
    from Core_Engines.Recursive_Improver import RecursiveImprover
except ImportError:
    # Fallback or mock if needed, but for now we assume it exists
    RecursiveImprover = None

class IntelligentDiscoveryAgent:
    """
    Agent responsible for discovering weaknesses and orchestrating self-improvement.
    It uses the RecursiveImprover to apply changes.
    """
    def __init__(self):
        self.improver = RecursiveImprover() if RecursiveImprover else None

    def scan_and_heal(self, target_module: str, diagnosis: str, improvement_plan: str) -> Dict[str, Any]:
        """
        Scans a target module and applies improvements based on a diagnosis and plan.
        """
        if not self.improver:
            return {"status": "error", "message": "RecursiveImprover not available"}

        print(f"🕵️ [Discovery] Scanning {target_module}...")
        print(f"   ⚠️ Diagnosis: {diagnosis}")
        print(f"   💡 Plan: {improvement_plan}")

        # Construct a detailed goal for the improver
        full_goal = f"""
        DIAGNOSIS: {diagnosis}
        
        IMPROVEMENT PLAN:
        {improvement_plan}
        
        Please analyze the code and apply these improvements.
        Ensure backward compatibility and add type hints.
        """

        # Execute improvement
        result = self.improver.analyze_and_improve(target_module, full_goal, apply_changes=True)
        
        return result

if __name__ == "__main__":
    # Test run if executed directly
    agent = IntelligentDiscoveryAgent()
    
    # Fix Volition Engine
    target = "Volition_Engine"
    diagnosis = "The 'self_improvement' drive is misinterpreted as 'optimization' (performance tuning) instead of 'code generation'."
    plan = """
    1. Modify 'generate_goal' method.
    2. When 'self_improvement' drive is dominant:
       - Set 'type' to 'self_improvement' (NOT 'optimization').
       - Set 'description' to 'Initiate recursive self-improvement cycle on a target module.'
       - Set 'reason' to 'Self-Improvement drive is active; seeking to evolve codebase.'
    3. Ensure 'curiosity' topics are dynamic or at least expanded.
    """
    
    result = agent.scan_and_heal(target, diagnosis, plan)
    print(f"Result: {result}")
