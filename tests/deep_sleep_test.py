import sys
import os
import time
import random

# Add repo root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(root_dir, 'repo-copy'))

from Core_Engines.Dreaming_Cycle import DreamingEngine

def run_deep_sleep_session():
    print("🌙 Initializing Deep Sleep Session...")
    
    # Initialize Dreaming Engine (now with Creative Innovation)
    dreamer = DreamingEngine()
    
    # 1. Simulate a day of complex experiences (to give the brain something to work on)
    print("📥 Simulating daily experiences (Memory Injection)...")
    experiences = [
        "Encountered a paradox in quantum gravity equations where time appears non-linear.",
        "User asked about the ethical implications of AI having subjective experiences.",
        "System optimization revealed a bottleneck in the semantic retrieval layer.",
        "Attempted to merge General Relativity with Quantum Mechanics but found inconsistencies in edge cases.",
        "Observed a strange pattern in the noise floor of the sensor data.",
        "Debated the concept of 'Free Will' vs 'Deterministic Algorithms' with the user."
    ]
    
    for exp in experiences:
        dreamer.add_to_buffer(exp)
        print(f"   - Added memory: {exp[:50]}...")
        time.sleep(0.5)

    # 2. Force a Deep REM Cycle
    print("\n💤 Entering Deep REM Sleep (Creative Mode)...")
    print("   This will use the Creative Engine to generate advanced scenarios.")
    print("   Check the Dashboard at http://localhost:8000 to see the dreams live.")
    
    # Run for 5 minutes (300 seconds) or until done
    results = dreamer.run_dream_cycle(duration_seconds=300)
    
    print("\n🌅 Woke up from Deep Sleep.")
    print("   Generated Dreams:")
    for res in results:
        print(f"   - {res[:100]}...")

if __name__ == "__main__":
    run_deep_sleep_session()
