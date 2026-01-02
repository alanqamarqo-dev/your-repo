import sys
import os

# Add path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "AGL_Core"))

from AGL_Core.AGL_Super_Intelligence import AGL_Super_Intelligence

def run_unified_lib_test():
    print("🔬 STARTING UNIFIED LIBRARY TEST...")
    
    # 1. Initialize ASI
    asi = AGL_Super_Intelligence()
    
    # 2. Verify Library Access
    if asi.lib:
        print("\n✅ [SUCCESS] Unified Library is accessible.")
        
        # Test Standard Lib
        print(f"   -> OS Name: {asi.lib.std.os.name}")
        print(f"   -> Random Number: {asi.lib.std.random.randint(1, 100)}")
        
        # Test Scientific Lib
        if asi.lib.sci.numpy:
            arr = asi.lib.sci.numpy.array([1, 2, 3])
            print(f"   -> NumPy Array: {arr}")
        else:
            print("   -> ⚠️ NumPy not found.")
            
        # Test Execution Context
        print("\n--- Testing Dynamic Execution ---")
        code = """
import math
result = math.sqrt(16) + np.sum([1, 2, 3])
"""
        context = asi.lib.execute_code(code)
        if isinstance(context, dict):
            print(f"   -> Execution Result: {context.get('result')}")
        else:
            print(f"   -> Execution Failed: {context}")
            
    else:
        print("\n❌ [FAILURE] Unified Library not found.")

if __name__ == "__main__":
    run_unified_lib_test()
