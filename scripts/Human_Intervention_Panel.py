import os
import sys
import time
from pathlib import Path

# Setup paths
ROOT = Path(__file__).parent.parent
ARTIFACTS = ROOT / 'artifacts'
CONTROLS_DIR = ARTIFACTS / 'controls'
STOP_FILE = CONTROLS_DIR / 'STOP'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("="*50)
    print("   🛡️  AGL HUMAN INTERVENTION PANEL  🛡️")
    print("="*50)
    print(f"Status: {'🔴 SYSTEM STOPPED' if STOP_FILE.exists() else '🟢 SYSTEM RUNNING'}")
    print("-" * 50)

def toggle_stop():
    if STOP_FILE.exists():
        try:
            os.remove(STOP_FILE)
            print("\n✅ EMERGENCY STOP REMOVED. System may resume.")
        except Exception as e:
            print(f"\n❌ Error removing STOP file: {e}")
    else:
        try:
            CONTROLS_DIR.mkdir(parents=True, exist_ok=True)
            with open(STOP_FILE, 'w') as f:
                f.write(f"STOPPED BY HUMAN AT {time.ctime()}")
            print("\n🛑 EMERGENCY STOP ACTIVATED! System should halt immediately.")
        except Exception as e:
            print(f"\n❌ Error creating STOP file: {e}")

def show_logs():
    log_file = ARTIFACTS / 'logs' / 'safety.log'
    print("\n📄 Recent Safety Logs:")
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-10:]:
                    print(line.strip())
        except Exception as e:
            print(f"Error reading logs: {e}")
    else:
        print("No logs found.")

def main():
    while True:
        clear_screen()
        print_header()
        print("\nOptions:")
        print("1. 🛑 TOGGLE EMERGENCY STOP (Kill Switch)")
        print("2. 📄 View Safety Logs")
        print("3. 🚪 Exit Panel")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            toggle_stop()
            input("\nPress Enter to continue...")
        elif choice == '2':
            show_logs()
            input("\nPress Enter to continue...")
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid option.")
            time.sleep(1)

if __name__ == "__main__":
    main()
