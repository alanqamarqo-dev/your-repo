import sys
import os
import time

# Ensure we can import from AGL_NextGen/src
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, "AGL_NextGen", "src")

if src_path not in sys.path:
    sys.path.insert(0, src_path)
sys.path.append(current_dir)

try:
    from agl.core.super_intelligence import AGL_Super_Intelligence
except ImportError:
    from AGL_NextGen.src.agl.core.super_intelligence import AGL_Super_Intelligence

def run_volition_test():
    print("⚡ INITIALIZING AGL SUPER INTELLIGENCE FOR VOLITION TEST...")
    agi = AGL_Super_Intelligence()
    
    print("\n🧪 RUNNING AUTONOMOUS VOLITION TEST")
    print("===============================================================")
    
    # Force state to allow activity
    agi.state = "AWAKE"
    agi.last_activity = time.time() - 100 # Emulate idleness
    
    # This calls autonomous_tick which now calls our Quantum Logic Check
    decision = agi.autonomous_tick()
    
    print("\n===============================================================")
    print(f"🏆 FINAL DECISION: {decision}")
    
    if decision:
        print("✅ System successfully chose and validated a goal.")
    else:
        print("❌ System chose to do nothing (or goal was rejected).")

if __name__ == "__main__":
    run_volition_test()
