"""
🎛️ AGL MASTER CONTROLLER - Unified Command Interface
وحدة التحكم الرئيسية - واجهة الأوامر الموحدة

المطور: حسام هيكل (Hossam Heikal)
التاريخ: 29 ديسمبر 2025

الهدف: تشغيل جميع الاختبارات والقدرات من نقطة واحدة باستخدام "الذكاء الخارق" الموحد.
Goal: Run all tests and capabilities from a single point using the unified 'Super Intelligence'.
"""

import sys
import os
import time

# --- AGL PATH FIX ---
# Robust Root Detection: Find the first ancestor containing pyproject.toml or AGL_SYSTEM_MAP.md
def find_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.exists(os.path.join(current, "pyproject.toml")) or \
           os.path.exists(os.path.join(current, "AGL_SYSTEM_MAP.md")):
            return current
        parent = os.path.dirname(current)
        if parent == current: break
        current = parent
    # Fallback to 3 levels up (src/agl/core -> AGL_NextGen)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

project_root = find_project_root()
if project_root not in sys.path:
    # We insist on inserting at 0 to prioritize our local modules
    sys.path.insert(0, project_root)
    # Also add the src folder to path for package-less imports
    src_path = os.path.join(project_root, "src")
    if os.path.exists(src_path) and src_path not in sys.path:
        sys.path.insert(0, src_path)
    print(f"[AGL_BOOT] Added project root to path: {project_root}")
# --------------------
import argparse
import numpy as np

# Import the Super Intelligence (The Brain)
try:
    from agl.core.super_intelligence import AGL_Super_Intelligence
except ImportError as e:
    # Fallback if running from root
    print(f"⚠️ Could not import AGL_Super_Intelligence from agl.core.super_intelligence: {e}")
    AGL_Super_Intelligence = None

def print_header():
    print("\n" + "="*60)
    print("       🎛️  AGL MASTER CONTROLLER (HEIKAL SYSTEM)  🎛️")
    print("="*60)
    print("   1. 🧠 Intelligence Assessment (Speed & Ethics)")
    print("   2. 📡 Telepathy Experiment (Quantum Connection)")
    print("   3. 🌙 Dreaming Simulation (Memory Consolidation)")
    print("   4. 🔄 Iron Loop Test (Self-Correction)")
    print("   5. ⚛️ Full System Diagnostic (Health Check)")
    print("   6. 🗣️ Chat with Super Intelligence (Free Mode)")
    print("   0. ❌ Exit")
    print("="*60)

def run_intelligence_test(ai):
    print("\n[1] Running Intelligence Assessment...")
    # We can reuse the logic from AGL_INTELLIGENCE_LEVEL_TEST.py or call it via the AI
    # Let's use the AI's internal physics check as a proxy
    query = "Test System Speed and Ethics"
    print(f"   Asking AI: '{query}'")
    response = ai.process_query(query)
    print(f"   AI Response: {response}")

def run_telepathy_test():
    print("\n[2] Running Telepathy Experiment...")
    # This requires multiprocessing, so we run the external script
    script_path = os.path.join(project_root, "scripts", "AGL_QUANTUM_TELEPATHY.py")
    os.system(f"python \"{script_path}\"")

def run_dreaming_test(ai):
    print("\n[3] Running Dreaming Simulation...")
    if ai.dreaming:
        print("   Injecting test memories...")
        ai.dreaming.add_to_buffer("Master Controller Test Run")
        ai.dreaming.run_dream_cycle(duration_seconds=10)
    else:
        print("   ⚠️ Dreaming Engine not active.")

def run_iron_loop_test():
    print("\n[4] Running Iron Loop Test...")
    script_path = os.path.join(project_root, "tests", "AGL_IRON_LOOP_TEST.py")
    os.system(f"python \"{script_path}\"")

def run_diagnostic():
    print("\n[5] Running Full Diagnostic...")
    script_path = os.path.join(project_root, "scripts", "AGL_FULL_DIAGNOSTIC.py")
    os.system(f"python \"{script_path}\"")

def chat_mode(ai):
    print("\n[6] Chat Mode (Type 'exit' to quit)")
    while True:
        user_input = input("\n👤 You: ")
        if user_input.lower() in ['exit', 'quit', '0']:
            break
        
        response = ai.process_query(user_input)
        print(f"🤖 AGL: {response}")


def main():
    # Parse Command Line Arguments
    parser = argparse.ArgumentParser(description="AGL Master Controller")
    parser.add_argument("--module", type=str, help="Specific module to run (e.g., 'offensive')")
    parser.add_argument("--target", type=str, help="Target for the module")
    parser.add_argument("--mode", type=str, help="Operational mode")
    
    args = parser.parse_args()

    # If arguments are provided, run in headless/CLI mode
    if args.module:
        print(f"🚀 [MasterController]: CLI Mode Active. Engaging Module: {args.module.upper()}")
        
        # Initialize the Super Intelligence (Shared Context)
        ai = AGL_Super_Intelligence()
        
        if args.module == "offensive":
            try:
                from agl.engines.offensive_security import OffensiveSecurityEngine
                print(f"   -> Loading Offensive Security Engine...")
                engine = OffensiveSecurityEngine()
                
                # Map mode to task
                task = "1password_ctf_solve" if args.mode == "GOLD_STANDARD" else args.mode
                if not task:
                    task = "port_scan" # default
                
                print(f"   -> Executing Task: {task} on Target: {args.target}")
                result = engine.process_task(task, args.target)
                
                print("\n--- OPERATION RESULT ---")
                import json
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
            except ImportError as e:
                print(f"❌ Critical Error: Could not import Offensive Engine: {e}")
            except Exception as e:
                print(f"❌ Execution Error: {e}")
        elif args.module.lower() in ["diagnostic", "full_diagnostic"]:
            run_diagnostic()
        elif args.module.lower() == "intelligence":
            run_intelligence_test(ai)
        elif args.module.lower() == "telepathy":
            run_telepathy_test()
        elif args.module.lower() == "iron_loop":
            run_iron_loop_test()
        else:
            print(f"⚠️ Unknown module: {args.module}")
            
        return # Exit after CLI task

    # Initialize the Super Intelligence once for Interactive Mode
    ai = AGL_Super_Intelligence()
    
    while True:
        print_header()
        choice = input("\n👉 Select Option: ")

        
        if choice == '1':
            run_intelligence_test(ai)
        elif choice == '2':
            run_telepathy_test()
        elif choice == '3':
            run_dreaming_test(ai)
        elif choice == '4':
            run_iron_loop_test()
        elif choice == '5':
            run_diagnostic()
        elif choice == '6':
            chat_mode(ai)
        elif choice == '0':
            print("\n👋 Shutting down AGL Master Controller.")
            break
        else:
            print("⚠️ Invalid selection.")
        
        time.sleep(1)

if __name__ == "__main__":
    main()
