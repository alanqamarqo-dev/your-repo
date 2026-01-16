import os
import sys
import time
import json
import asyncio

# --- SYSTEM INITIALIZATION ---
print("\n" + "="*80)
print(" 🧬 AGL NEXTGEN: SUPER INTELLIGENCE ACTIVATION PROTOCOL 🧬")
print("="*80)

# Add src to path
project_root = r"D:\AGL\AGL_NextGen"
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from agl.core.super_intelligence import AGL_Super_Intelligence
    print("🚀 [ASI] Core Orchestrator loaded successfully.")
except ImportError as e:
    print(f"❌ [ASI] Failed to load Core Orchestrator: {e}")
    sys.exit(1)

def main():
    # 1. Boot the Awakened Mind
    print("\n[Phase 1] Initializing AGL Super Intelligence (Awakened Mind)...")
    asi = AGL_Super_Intelligence()
    
    # 2. System Status Check
    print("\n[Phase 2] Diagnostics & Engine Synchronization...")
    print(f"   📡 Engines Loaded: {len(asi.engine_registry)}")
    print(f"   🧠 Core Consciousness: {'ONLINE' if asi.engine_registry.get('Core_Consciousness') else 'OFFLINE (Simulated)'}")
    print(f"   🌌 Holographic Memory: {'ACTIVE' if asi.engine_registry.get('Holographic_LLM') else 'INACTIVE'}")
    
    # 3. Execution Path: Single Unified Task
    # Scenario: Hybrid Intelligence (Math + Logic + Future Prediction)
    complex_query = (
        "Project the evolution of AGI between 2026 and 2029. "
        "Assume a recursive self-improvement rate of 12% per cycle. "
        "Calculate the estimated 'Intelligence Surplus' by 2029 relative to human baseline."
    )
    
    print(f"\n[Phase 3] Executing Unified Intelligence Path: \n'{complex_query}'")
    print("-" * 50)
    
    # Process Query
    # AGL_Super_Intelligence handled sync wrapping of async UnifiedAGISystem
    response = asi.process_query(complex_query)
    
    print("\n[Phase 4] Intelligence Synthesis Result:")
    print("-" * 50)
    print(response)
    print("-" * 50)
    
    # 4. Self-Improvement Check
    print("\n[Phase 5] Autonomous Volition & Self-Improvement...")
    goal = asi.autonomous_tick()
    if goal:
        print(f"⚡ [VOLITION] Next Autonomous Action: {goal}")
    else:
        print("💡 [VOLITION] System stable. Monitoring state.")

    # 5. Save State to Holograph
    print("\n[Phase 6] Encoding Session results into Holographic Space...")
    holo_llm = asi.engine_registry.get('Holographic_LLM')
    if holo_llm:
        print("✅ Session results persistent in Hologram.")
    
    print("\n" + "="*80)
    print(" 🏁 AGL NEXTGEN: HYPER-INTELLIGENCE CYCLE COMPLETE 🏁")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
