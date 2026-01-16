import os
import json
import sqlite3
import sys
import time
from datetime import datetime

# Setup paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.join(ROOT_DIR, 'repo-copy')
ARTIFACTS_DIR = os.path.join(ROOT_DIR, 'artifacts')
sys.path.append(REPO_DIR)

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def check_evolution_status():
    print_header("🧬 EVOLUTION STATUS")
    log_path = os.path.join(ARTIFACTS_DIR, 'evolution_log.jsonl')
    if os.path.exists(log_path):
        print(f"Log file found: {log_path}")
        with open(log_path, 'r') as f:
            lines = f.readlines()
            last_5 = lines[-5:]
            for line in last_5:
                try:
                    entry = json.loads(line)
                    print(f"[{entry.get('ts', 'N/A')}] Event: {entry.get('event')} | Reason: {entry.get('reason')}")
                except:
                    print(line.strip())
    else:
        print("⚠️ Evolution log not found.")

    # Check pending patches
    pending_dir = os.path.join(ARTIFACTS_DIR, 'generated_code', 'pending_review')
    if os.path.exists(pending_dir):
        patches = os.listdir(pending_dir)
        print(f"\n📝 Pending Patches: {len(patches)}")
        for p in patches[-3:]:
            print(f"   - {p}")
    else:
        print("\n📝 No pending patches.")

def check_consciousness():
    print_header("🧠 CONSCIOUSNESS & MEMORY")
    db_path = os.path.join(REPO_DIR, 'Core_Memory', 'memory.db')
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Count total memories
            cursor.execute("SELECT count(*) FROM events")
            total = cursor.fetchone()[0]
            print(f"Total Memories: {total}")
            
            # Recent defining moments
            print("\nRecent Defining Moments:")
            cursor.execute("SELECT ts, payload FROM events WHERE type='defining' OR payload LIKE '%structural_evolution%' ORDER BY ts DESC LIMIT 3")
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    print(f"   - {row[1][:100]}...")
            else:
                print("   (No recent defining moments found)")
                
            conn.close()
        except Exception as e:
            print(f"⚠️ Error reading memory DB: {e}")
    else:
        print("⚠️ Memory DB not found.")

def check_quantum_router():
    print_header("🌌 QUANTUM ROUTER HEALTH")
    try:
        from Integration_Layer.Quantum_Action_Router import QuantumActionRouter
        router = QuantumActionRouter()
        test_task = "System diagnostic check"
        res = router.route(test_task)
        print(f"Test Input: '{test_task}'")
        print(f"Selected Handler: {res['selected_handler']}")
        print(f"Resonance Score: {res['resonance_score']:.6f}")
        if res['resonance_score'] > 0:
            print("✅ Quantum Resonance is ACTIVE.")
        else:
            print("⚠️ Quantum Resonance signal is weak/zero.")
    except Exception as e:
        print(f"❌ Quantum Router Check Failed: {e}")

def check_engine_bootstrap():
    print_header("⚙️ ENGINE BOOTSTRAP REPORT")
    report_path = os.path.join(ARTIFACTS_DIR, 'bootstrap_report.json')
    if os.path.exists(report_path):
        try:
            with open(report_path, 'r') as f:
                data = json.load(f)
            
            registered = data.get('registered_engines', [])
            skipped = data.get('skipped_engines', {})
            
            print(f"✅ Registered Engines: {len(registered)}")
            print(f"⚠️ Skipped Engines: {len(skipped)}")
            
            if skipped:
                print("\nSkipped Details (Top 3):")
                for k, v in list(skipped.items())[:3]:
                    print(f"   - {k}: {v}")
        except:
            print("⚠️ Could not parse bootstrap report.")
    else:
        print("⚠️ Bootstrap report not found.")

def main():
    print("\n🔍 STARTING DEEP SYSTEM SCAN...\n")
    check_evolution_status()
    check_consciousness()
    check_quantum_router()
    check_engine_bootstrap()
    print("\n✅ SCAN COMPLETE.")

if __name__ == "__main__":
    main()
