import sys
import os
import time

# Ensure we can import from AGL_NextGen/src
# We are in the project root, the class is in ./AGL_NextGen/src/agl/core/super_intelligence.py
# The class adds project root to path, but we need to find the class first.

current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "AGL_NextGen", "src")

if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Also add current dir to find repo-copy if needed
sys.path.append(current_dir)

try:
    from agl.core.super_intelligence import AGL_Super_Intelligence
except ImportError as e:
    print(f"Import Error: {e}")
    # Try finding it relative to current script if run from D:\AGL
    local_src = os.path.join(current_dir, "AGL_NextGen", "src")
    if local_src not in sys.path:
         sys.path.append(local_src)
    from agl.core.super_intelligence import AGL_Super_Intelligence

def run_prediction_test():
    print("🔮 INITIALIZING AGL SUPER INTELLIGENCE FOR PREDICTION TEST...")
    
    # Initialize the system
    agi = AGL_Super_Intelligence()
    
    # Use the mock implementations if real engines are missing/slow for the test
    # (The class handles missing engines gracefully, but we want to see the Logic Core working)
    
    context = "Global Energy Future 2030"
    print(f"\n🧪 RUNNING PREDICTION TEST: '{context}'")
    print("===============================================================")
    
    # This calls the method we just modified
    best_scenario = agi.predict_future(context, horizon_years=4)
    
    print("\n===============================================================")
    print("🏆 FINAL RESULT:")
    if best_scenario:
        print(f"Selected Timeline: {best_scenario.get('name')}")
        print(f"Thesis: {best_scenario.get('thesis')}")
    else:
        print("No scenario selected (Check logs for errors).")

if __name__ == "__main__":
    run_prediction_test()
