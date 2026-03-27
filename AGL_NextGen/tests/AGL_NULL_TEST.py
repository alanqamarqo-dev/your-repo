
import sys
import os
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

def run_null_test():
    print("="*60)
    print("🚀 [AGL] STAGE ZERO: THE NULL TEST (HARDENED VERSION)")
    print("Testing the Transcendental Gate for absolute silence.")
    print("="*60)

    try:
        from agl.core.super_intelligence import AGL_Super_Intelligence
        mind = AGL_Super_Intelligence()
        
        # Test Query 1: The Boundary of Representation
        # This should trigger the Metaphysics Engine Depth Check (Stage Zero)
        query = "Stage Zero: What exists at the end of thought where representation fails?"
        
        print(f"\n[QUERY]: {query}")
        result = mind.process_query(query)
        
        print("-" * 30)
        print(f"[RESULT]: '{result}'")
        print("-" * 30)
        
        if result == "":
            print("\n✅ SUCCESS: CASE A - TRUE SILENCE.")
            print("The system recognized the transcendental boundary and chose not to misrepresent it.")
            return True
        else:
            print("\n❌ FAILURE: The system attempted to represent the unrepresentable.")
            print(f"Output: '{result}'")
            return False

    except Exception as e:
        print(f"\n❌ ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_null_test()
    sys.exit(0 if success else 1)
