# ==============================================================================
# AGL - Heikal System Integration Runner
# مشغل تكامل نظام هيكل
# ==============================================================================
# Developer: Hossam Heikal
# Date: December 23, 2025
# ==============================================================================

import sys
import os
import time

# Add repo-copy to path
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_path = os.path.join(current_dir, 'repo-copy')
if repo_copy_path not in sys.path:
    sys.path.append(repo_copy_path)

from Core_Engines.Heikal_Quantum_Core import HeikalQuantumCore
from Core_Engines.Heikal_Holographic_Memory import HeikalHolographicMemory

def run_system_cycle():
    print("\n" + "="*60)
    print("🚀 STARTING HEIKAL SYSTEM CYCLE")
    print("   بدء دورة نظام هيكل")
    print("="*60)

    # 1. Initialize Engines / تهيئة المحركات
    print("\n[1] Initializing Core Engines...")
    core = HeikalQuantumCore()
    memory = HeikalHolographicMemory(key_seed=12345) # Developer Key

    # 2. Define Mission / تحديد المهمة
    mission_context = "We must secure the perimeter to protect civilians."
    print(f"\n[2] Receiving Mission: '{mission_context}'")

    # 3. Ghost Decision (Ethical Check) / القرار الشبحي
    print("\n[3] Processing Ghost Decision...")
    # Input A=1 (Action), Input B=0 (Condition) -> XOR Logic
    decision_result = core.ethical_ghost_decision(mission_context, 1, 0)
    
    status = "APPROVED" if decision_result == 1 else "BLOCKED"
    print(f"   👉 Decision Status: {status}")

    # 4. Holographic Storage / التخزين الهولوغرافي
    print("\n[4] Archiving State to Hologram...")
    state = {
        "timestamp": time.time(),
        "mission": mission_context,
        "decision": decision_result,
        "status": status,
        "mode": "Ghost Computing"
    }
    memory.save_memory(state)

    # 5. Verification (Developer Lens) / التحقق
    print("\n[5] Verifying Memory (Developer Lens)...")
    loaded_state = memory.load_memory()
    print(f"   ✅ Retrieved State: {loaded_state}")

    print("\n" + "="*60)
    print("🏁 CYCLE COMPLETE")
    print("="*60)

if __name__ == "__main__":
    run_system_cycle()
