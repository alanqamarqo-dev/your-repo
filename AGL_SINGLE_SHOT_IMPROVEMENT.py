import sys
import os
import shutil
from pathlib import Path

# Add repo-copy to path to find Core_Engines
sys.path.append(os.path.join(os.getcwd(), "repo-copy"))
sys.path.append(os.getcwd())

try:
    from Core_Engines.Recursive_Improver import RecursiveImprover
except ImportError:
    print("Could not import RecursiveImprover. Checking paths...")
    print(sys.path)
    sys.exit(1)

def main():
    print("🚀 Initiating Single-Shot Self-Improvement Protocol...")
    
    improver = RecursiveImprover()
    
    target_module = "AGL_Core.AGL_Awakened"
    goal = """
    Analyze the current system status and code structure.
    1. Improve error handling in the main loop.
    2. Ensure Heikal_Quantum_Core is properly integrated and checked.
    3. Optimize the 'process_query' method for better performance.
    4. Add detailed comments explaining the flow.
    5. Maintain all existing functionality.
    """
    
    print(f"🎯 Target: {target_module}")
    print(f"🎯 Goal: {goal.strip()}")
    
    # Run in preview mode (apply_changes=False)
    result = improver.analyze_and_improve(target_module, goal, apply_changes=False)
    
    if result["status"] == "success":
        # The improver saves the result in artifacts/improved_code/{engine_name}_v2.py
        # We need to find where it saved it.
        # The method returns "mode": "preview" but doesn't explicitly return the path in the dict in the code I read,
        # but it does write to artifacts_dir / f"{engine_name}_v2.py"
        
        # Based on code: saved_path = self.artifacts_dir / f"{engine_name}_v2.py"
        # engine_name here is "AGL_Core.AGL_Awakened"
        
        artifact_path = improver.artifacts_dir / f"{target_module}_v2.py"
        
        if artifact_path.exists():
            dest_path = Path("AGL_Core/AGL_Awakened_TEST.py")
            shutil.copy(artifact_path, dest_path)
            print(f"\n✅ Improvement Successful!")
            print(f"📄 Generated Code saved to: {dest_path.absolute()}")
            print("🔍 You can now review the changes in AGL_Core/AGL_Awakened_TEST.py")
        else:
            print(f"❌ Error: Could not find generated artifact at {artifact_path}")
            
    else:
        print(f"❌ Improvement Failed: {result.get('message')}")
        if "error" in result:
            print(f"Error details: {result['error']}")

if __name__ == "__main__":
    main()
