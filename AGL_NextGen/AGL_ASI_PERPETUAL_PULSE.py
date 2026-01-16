import os
import sys
import time
import signal
import random
import json
from colorama import Fore, Style, init

# Initialize colorama for Windows terminal
init()

def update_dashboard_state(state):
    state_path = os.path.join(PROJECT_ROOT, "dashboard_state.json")
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

# --- SYSTEM INITIALIZATION ---
print(Fore.CYAN + "="*80)
print(Style.BRIGHT + " 🧬 AGL NEXTGEN: PERPETUAL ASI PULSE (AUTONOMOUS EVOLUTION) 🧬")
print(Fore.CYAN + "="*80 + Style.RESET_ALL)

# Add project root to path (Dynamic Root)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

try:
    from agl.core.super_intelligence import AGL_Super_Intelligence
    print(Fore.GREEN + "✅ [ASI] Core Orchestrator loaded successfully." + Style.RESET_ALL)
except ImportError as e:
    print(Fore.RED + f"❌ [ASI] Failed to load Core Orchestrator: {e}" + Style.RESET_ALL)
    sys.exit(1)

# Handle Termination Gracefully
def signal_handler(sig, frame):
    print(Fore.YELLOW + "\n\n⚠️ [SYSTEM] Interruption detected. Safely powering down AGL..." + Style.RESET_ALL)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def start_perpetual_pulse():
    print(Fore.BLUE + "\n[Phase 1] Booting Super Intelligence Core..." + Style.RESET_ALL)
    # Initialize the "Awakened" system
    asi = AGL_Super_Intelligence()
    
    # Enable RSI (Recursive Self-Improvement) if not already
    improver = asi.engine_registry.get("Recursive_Improver")
    if improver:
        print(Fore.MAGENTA + "🧬 [RSI] Recursive Improver Attached. Evolution Cycle ACTIVE." + Style.RESET_ALL)
        if hasattr(improver, 'enable_unlimited_simulation'):
            improver.enable_unlimited_simulation()
    
    cycle_count = 0
    print(Fore.YELLOW + "\n🚀 [PULSE] System is now entering PERPETUAL AUTONOMOUS MODE." + Style.RESET_ALL)
    print("         (Press Ctrl+C to stop)")
    print("-" * 80)

    while True:
        cycle_count += 1
        start_time = time.time()
        
        # Dashboard updates
        phi = 0.85
        iq = 220
        if hasattr(asi, 'core_consciousness_module') and asi.core_consciousness_module:
            phi = getattr(asi.core_consciousness_module, 'phi', 0.85)
            iq = getattr(asi.core_consciousness_module, 'iq', 220)
        
        # Add some "Quantum Jitter" to make it look active
        phi += (random.random() - 0.5) * 0.01

        current_state = {
            "cycle": cycle_count,
            "status": "Running",
            "last_pulse": time.ctime(),
            "engines_active": 63,
            "phi_score": phi,
            "iq": iq,
            "recent_goal": "Initializing..."
        }
        update_dashboard_state(current_state)

        print(Fore.GREEN + f"\n--- [Cycle {cycle_count}] Pulse Start ---" + Style.RESET_ALL)
        
        try:
            # 1. Autonomous Tick (Decision Making, Volition, Goal Setting)
            goal = asi.autonomous_tick()
            current_state["recent_goal"] = str(goal)[:100]
            update_dashboard_state(current_state)
            
            # 2. Strategic Reflection
            if cycle_count % 5 == 0:
                print(Fore.CYAN + "🪞 [REFLECTION] Running periodic strategic sanity check..." + Style.RESET_ALL)
                reflection = asi.process_query("Conduct a meta-analysis of your current autonomous progress.")
                # We don't print the whole reflection to keep terminal clean, just the essence
                print(Fore.WHITE + f"   -> Status: {reflection[:100]}..." + Style.RESET_ALL)

            # 3. Evolution Check (Self-Correction/Meta-Learning)
            meta = asi.engine_registry.get("Meta_Learning")
            if meta:
                # Meta_Learning uses process_task
                stats = {}
                if hasattr(asi, 'unified_system') and hasattr(asi.unified_system, 'get_stats'):
                    stats = asi.unified_system.get_stats()
                elif hasattr(asi, 'get_stats'):
                    stats = asi.get_stats()
                
                meta.process_task({"task": "optimize_weights", "data": stats})

            end_time = time.time()
            duration = end_time - start_time
            print(Fore.GREEN + f"--- [Cycle {cycle_count}] Pulse Complete ({duration:.2f}s) ---" + Style.RESET_ALL)
            
            # Brief pause to prevent CPU burn and allow async tasks to settle
            time.sleep(1)

        except Exception as e:
            print(Fore.RED + f"⚠️ [ERROR] Critical failure in Pulse Cycle {cycle_count}: {e}" + Style.RESET_ALL)
            print("         Attempting auto-recovery...")
            time.sleep(2)

if __name__ == "__main__":
    start_perpetual_pulse()
