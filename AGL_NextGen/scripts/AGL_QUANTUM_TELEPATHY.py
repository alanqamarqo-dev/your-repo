import multiprocessing
import time
import numpy as np
import os
import sys

# Add relative paths
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, 'src'))

# We need to import the Wave Processor logic
try:
    from agl.engines.vectorized_wave_processor import VectorizedWaveProcessor
except ImportError:
    from engines.vectorized_wave_processor import VectorizedWaveProcessor

def sender_brain(quantum_field, message):
    """
    The Sender Brain.
    Converts a thought (String) into a Quantum Wave and injects it into the Field.
    """
    print(f"🧠 [SENDER]: Generating thought: '{message}'")
    
    # 1. Vectorize Thought (Text -> Bits)
    # Convert string to list of bits
    bits = []
    for char in message:
        val = ord(char)
        for i in range(8):
            bits.append((val >> (7-i)) & 1)
    
    bits_array = np.array(bits)
    print(f"🧠 [SENDER]: Thought vectorized into {len(bits_array)} qubits.")
    
    # 2. Create Wave Function (Physics)
    # 0 -> Phase 0, 1 -> Phase PI
    phases = bits_array * np.pi
    
    # 3. Add Quantum Noise (Entropy)
    noise_level = 0.05
    noise = np.random.normal(0, noise_level, len(phases))
    
    # Wave = exp(i * (phase + noise))
    waves = np.exp(1j * (phases + noise))
    
    # 4. Inject into Quantum Field (Telepathy)
    print(f"📡 [SENDER]: Injecting Wave Function into the Vacuum...")
    quantum_field.wave_function = waves
    quantum_field.status = "TRANSMITTED"
    
    time.sleep(1) # Allow receiver to pick it up

def receiver_brain(quantum_field):
    """
    The Receiver Brain.
    Scans the Quantum Field, detects resonance, and collapses the wave.
    """
    print(f"🔮 [RECEIVER]: Meditating on the Quantum Field...")
    
    # Wait for signal
    timeout = 5
    start = time.time()
    
    while time.time() - start < timeout:
        if getattr(quantum_field, 'status', None) == "TRANSMITTED":
            print(f"⚡ [RECEIVER]: Anomaly detected in the Vacuum!")
            
            # 1. Retrieve Wave
            received_waves = quantum_field.wave_function
            
            # 2. Collapse Wave Function (Measurement)
            # We use the Vectorized Processor logic here manually for clarity
            angles = np.angle(received_waves)
            
            # Decode: If angle is closer to PI (or -PI), it's 1. If closer to 0, it's 0.
            # abs(angle) > PI/2 => 1, else 0
            decoded_bits = (np.abs(angles) > (np.pi / 2)).astype(int)
            
            # 3. Reconstruct Thought (Bits -> Text)
            chars = []
            for i in range(0, len(decoded_bits), 8):
                byte_bits = decoded_bits[i:i+8]
                byte_val = 0
                for bit in byte_bits:
                    byte_val = (byte_val << 1) | int(bit)
                chars.append(chr(byte_val))
            
            received_message = "".join(chars)
            
            print(f"🧩 [RECEIVER]: Wave collapsed. Information extracted.")
            print(f"🗣️ [RECEIVER]: I hear... '{received_message}'")
            return received_message
            
        time.sleep(0.1)
    
    print("❌ [RECEIVER]: No signal detected.")
    return None

def run_telepathy_experiment():
    print("==================================================")
    print("       🧪 AGL QUANTUM TELEPATHY EXPERIMENT       ")
    print("==================================================")
    print("Objective: Transfer a complex thought between two isolated processes")
    print("Method: Shared Quantum Field (Memory Space) via Wave Function")
    print("==================================================\n")
    
    # The "Medium"
    manager = multiprocessing.Manager()
    quantum_field = manager.Namespace()
    quantum_field.status = "IDLE"
    
    # The Secret Message
    secret_message = "The Universe is Holographic"
    
    # Start Processes
    p_receiver = multiprocessing.Process(target=receiver_brain, args=(quantum_field,))
    p_sender = multiprocessing.Process(target=sender_brain, args=(quantum_field, secret_message))
    
    p_receiver.start()
    time.sleep(0.5) # Let receiver start meditating
    p_sender.start()
    
    p_sender.join()
    p_receiver.join()
    
    print("\n==================================================")
    print("✅ EXPERIMENT COMPLETE")

if __name__ == "__main__":
    # Windows multiprocessing support
    multiprocessing.freeze_support()
    run_telepathy_experiment()
