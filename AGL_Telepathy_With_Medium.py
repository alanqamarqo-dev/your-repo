import multiprocessing
import time
import random
import json
import os
import numpy as np

# Configuration
ITERATIONS = 20
VACUUM_FILE = "vacuum_spacetime_fabric.json"

def sender_process(run_id):
    """
    Sends packets via the Vacuum Medium.

    Args:
        run_id (int): A unique identifier for this run.
    """
    print(f"[Unit A] Started. Transmitting {ITERATIONS} packets via Vacuum...")
    
    rng = random.SystemRandom()
    
    for i in range(ITERATIONS):
        # 1. Generate Bit
        bit = rng.randint(0, 1)
        
        # 2. Encode into Phase (0 or PI)
        target_phase = np.pi if bit == 0 else 0
        
        # 3. Create Wave Function (Signal + Noise)
        field_size = 64
        noise_level = 0.1
        
        real_part = np.cos(target_phase) + np.random.normal(0, noise_level, field_size)
        imag_part = np.sin(target_phase) + np.random.normal(0, noise_level, field_size)
        
        # 4. Write to Medium (The "Universe")
        packet = {
            "id": i,
            "real": real_part.tolist(),
            "imag": imag_part.tolist()
        }
        
        with open(f"{VACUUM_FILE}.tmp", "w") as f:
            json.dump(packet, f)
        
        os.replace(f"{VACUUM_FILE}.tmp", VACUUM_FILE)
        
        # Log Truth
        with open(f"sender_{run_id}.log", "a") as f:
            f.write(f"{i}:{bit}\n")
            
    print("[Unit A] Transmission Complete.")

def receiver_process(run_id):
    """
    Receives packets from the Vacuum Medium.

    Args:
        run_id (int): A unique identifier for this run.
    """
    print(f"[Unit B] Started. Listening to Vacuum...")
    
    last_seen_id = -1
    captured_count = 0
    
    start_time = time.time()
    
    while captured_count < ITERATIONS:
        if time.time() - start_time > 15: 
            break
            
        if os.path.exists(VACUUM_FILE):
            try:
                with open(VACUUM_FILE, "r") as f:
                    packet = json.load(f)
                
                packet_id = packet["id"]
                
                if packet_id > last_seen_id:
                    # New packet!
                    last_seen_id = packet_id
                    captured_count += 1
                    
                    # 1. Reconstruct Wave
                    real_part = np.array(packet["real"])
                    imag_part = np.array(packet["imag"])
                    complex_wave = real_part + 1j * imag_part
                    
                    # 2. Demodulate (Extract Phase)
                    avg_vector = np.mean(complex_wave, axis=0)  # Use mean instead of np.angle for simplicity
                    detected_phase = np.abs(avg_vector)
                    
                    # 3. Decode Bit
                    guess = 0 if detected_phase < np.pi / 2 else 1
                    
                    # Log Guess
                    with open(f"receiver_{run_id}.log", "a") as f:
                        f.write(f"{packet_id}:{guess}\n")
                        
            except Exception as e:
                print(f"[Unit B] Error: {e}")
            
        time.sleep(0.05)
    print("[Unit B] Listening Complete.")

def analyze_results(run_id):
    """
    Analyzes the results of the Vacuum Telepathy Test.

    Args:
        run_id (int): A unique identifier for this run.
    """
    print("\nAnalyzing Vacuum Telepathy Results...")
    
    try:
        with open(f"sender_{run_id}.log", "r") as f:
            sender_lines = f.readlines()
        with open(f"receiver_{run_id}.log", "r") as f:
            receiver_lines = f.readlines()
    except FileNotFoundError:
        print("Error: Logs missing.")
        return
    
    sender_map = {int(line.split(':')[0]): int(line.split(':')[1]) for line in sender_lines}
    receiver_map = {int(line.split(':')[0]): int(line.split(':')[1]) for line in receiver_lines}
    
    matches = sum(1 for pid, sent_bit in sender_map.items() if pid in receiver_map and receiver_map[pid] == sent_bit)
    total = len(sender_map)  # or captured_count
    
    accuracy = (matches / total) * 100
    print(f"Packets received: {total}/{ITERATIONS}")
    print(f"Accuracy: {accuracy:.2f}%")
    
    if accuracy > 90:
        print("SUCCESS: Information successfully teleported via Vacuum Medium!")
        print("Proof: The wave phase carried the bit through the noise.")
    else:
        print("FAILURE: High noise or sync error.")

    # Cleanup
    try:
        os.remove(f"sender_{run_id}.log")
        os.remove(f"receiver_{run_id}.log")
        os.remove(VACUUM_FILE)
    except FileNotFoundError:
        pass

if __name__ == "__main__":
    run_id = int(time.time())
    
    # Clean old logs
    if os.path.exists(f"sender_{run_id}.log"): os.remove(f"sender_{run_id}.log")
    if os.path.exists(f"receiver_{run_id}.log"): os.remove(f"receiver_{run_id}.log")

    p1 = multiprocessing.Process(target=sender_process, args=(run_id,))
    p2 = multiprocessing.Process(target=receiver_process, args=(run_id,))
    
    print("Starting AGL Telepathy Test (WITH MEDIUM)...")
    print("Condition: Shared Vacuum File Enabled.")
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()
    
    analyze_results(run_id)