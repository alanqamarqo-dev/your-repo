import sys
import os
import time
from pathlib import Path
import importlib

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))
sys.path.append(os.getcwd()) # Ensure root is in path for dummy import

from Core_Engines.Recursive_Improver import RecursiveImprover

def main():
    print("🧬 [DEMO] Starting Evolution Demo...")
    
    # 1. Setup Dummy Target (Ensure it exists)
    target_file = Path("AGL_Dummy_Target.py")
    if not target_file.exists():
        target_file.write_text('def hello():\n    print("Hello world")', encoding="utf-8")
    
    print(f"   📄 Target: {target_file}")
    print(f"   📜 Original Content:\n{target_file.read_text()}")

    # 2. Initialize Improver
    improver = RecursiveImprover()
    
    # 3. Run Evolution
    goal = "Add a docstring explaining the function, and change it to print the message 3 times using a loop."
    print(f"   🚀 Requesting Evolution: '{goal}'")
    
    # We pass the module name "AGL_Dummy_Target"
    # The improver uses importlib, so it needs to be importable.
    
    result = improver.analyze_and_improve(
        engine_name="AGL_Dummy_Target", 
        improvement_goal=goal,
        apply_changes=True
    )
    
    print(f"   📝 Result Status: {result.get('status')}")
    
    if result.get('status') == 'success':
        print("\n✅ [SUCCESS] Evolution Applied!")
        print("   📄 New Code Content:")
        print("-" * 40)
        print(target_file.read_text(encoding="utf-8"))
        print("-" * 40)
        
        # Verify backup
        if 'backup' in result:
            print(f"   🛡️ Backup saved at: {result['backup']}")
            
    else:
        print(f"\n❌ [FAIL] Evolution Failed: {result.get('message')}")
        if 'error' in result:
            print(f"   Error Details: {result['error']}")

if __name__ == "__main__":
    main()
