import multiprocessing
import time
import random
import json
import os
import numpy as np
import sys

# Configuration
ITERATIONS = 100
DELAY = 0.05 # 50ms to be fast but distinct

def sender_process(run_id):
    """
    Unit A: The Sender
    Generates True Random Numbers (SystemRandom).
    Does NOT share them.
    Does NOT write to shared memory.
    """
    results = []
    # Use SystemRandom to ensure no pseudo-random synchronization is possible
    rng = random.SystemRandom()
    
    print(f"[Unit A] Started. Generating {ITERATIONS} bits...")
    for i in range(ITERATIONS):
        # Generate X ∈ {0,1}
        x = rng.randint(0, 1)
        timestamp = time.time()
        
        # Log locally (private memory)
        results.append({"i": i, "t": timestamp, "val": x})
        
        # Sleep to sync roughly with B (but no exact lock)
        time.sleep(DELAY)
        
    # Write private log for post-mortem analysis only
    with open(f"sender_{run_id}.json", "w") as f:
        json.dump(results, f)
    print("[Unit A] Finished.")

def receiver_process(run_id):
    """
    Unit B: The Receiver
    Tries to predict X.
    Constraint: No shared file, no shared memory.
    Relies on: Internal Logic / Local Wave State.
    """
    results = []
    print(f"[Unit B] Started. Attempting to sense {ITERATIONS} bits...")
    
    for i in range(ITERATIONS):
        # Attempt to sense the value.
        # Since we are strictly forbidden from using the "Vacuum File" (Medium),
        # Unit B can only rely on "Local Vacuum Fluctuations" (Local Noise).
        
        # Heikal Logic: Without a medium, the wave cannot propagate.
        # So we measure local ZPE (Zero Point Energy).
        local_phase = np.random.uniform(0, 2*np.pi)
        
        # Decode local phase
        # If phase is in upper hemisphere -> 1, else 0
        guess = 1 if 0 <= local_phase < np.pi else 0
        
        timestamp = time.time()
        results.append({"i": i, "t": timestamp, "val": guess})
        time.sleep(DELAY)
        
    # Write private log for post-mortem analysis only
    with open(f"receiver_{run_id}.json", "w") as f:
        json.dump(results, f)
    print("[Unit B] Finished.")

def analyze_results(run_id):
    print("\n📊 Analyzing Double-Blind Results...")
    try:
        with open(f"sender_{run_id}.json", "r") as f:
            sender_data = json.load(f)
        with open(f"receiver_{run_id}.json", "r") as f:
            receiver_data = json.load(f)
    except FileNotFoundError:
        print("❌ Error: Logs not found.")
        return

    matches = 0
    total = len(sender_data)
    
    # Compare bit by bit
    # Note: Since they run in parallel with sleep, indices should align roughly.
    for s, r in zip(sender_data, receiver_data):
        if s["val"] == r["val"]:
            matches += 1
            
    accuracy = (matches / total) * 100
    
    print(f"Total Trials: {total}")
    print(f"Matches: {matches}")
    print(f"Accuracy: {accuracy:.2f}%")
    
    print("\n🔎 Scientific Conclusion:")
    if 45 < accuracy < 55:
        print("✅ Result: ~50% (Random Chance).")
        print("   Interpretation: No information transfer occurred.")
        print("   Reason: The 'Vacuum Medium' (Shared File) was removed.")
        print("   Proof: Ghost Computing requires a medium to transmit waves.")
    elif accuracy > 60:
        print("⚠️ Result: > 60% (Statistically Significant).")
        print("   Interpretation: Anomalous correlation detected!")
    else:
        print(f"   Result: {accuracy:.2f}% (Inconclusive/Noise).")

    # Cleanup
    try:
        os.remove(f"sender_{run_id}.json")
        os.remove(f"receiver_{run_id}.json")
    except:
        pass

if __name__ == "__main__":
    # Ensure clean start
    run_id = int(time.time())
    
    # Create independent processes
    p1 = multiprocessing.Process(target=sender_process, args=(run_id,))
    p2 = multiprocessing.Process(target=receiver_process, args=(run_id,))
    
    print("🚀 Starting AGL Telepathy Test (Strict Isolation Mode)...")
    print("   Condition: No Shared Files, No Shared Memory.")
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()
    
    analyze_results(run_id)
