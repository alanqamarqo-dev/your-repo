import subprocess
import sys
import os
import time
import collections

# System Settings
# Use absolute path to ensure we find the exe
current_dir = os.path.dirname(os.path.abspath(__file__))
EXE_PATH = os.path.join(current_dir, "agl_camera.exe")
MEMORY_SIZE = 20  # Short-term memory (last 20 readings)

print("🧠 [HERMES] INITIALIZING NEURAL INTERPRETER...")

if not os.path.exists(EXE_PATH):
    print(f"❌ Error: Camera executable not found at {EXE_PATH}")
    sys.exit()

# Buffer for past data (to analyze pattern over time)
flux_memory = collections.deque(maxlen=MEMORY_SIZE)

def analyze_pattern(memory):
    if len(memory) < MEMORY_SIZE: return "INITIALIZING...", "WHITE"
    
    avg_flux = sum(memory) / len(memory)
    max_flux = max(memory)
    
    # --- Calibrated Logic ---
    
    # 1. Deep Thought State (Zen Mode)
    if avg_flux < 1.0:
        return "🌌 STATE: DEEP THOUGHT (System Idle)", "\033[94m" # Blue
    
    # 2. Focused Work State (Flow State)
    elif 1.0 <= avg_flux < 8.0:
        return "👁️ STATE: FOCUSED WORK (Active)", "\033[92m" # Green
        
    # 3. Creative Surge State (Chaos/Creativity)
    elif avg_flux >= 8.0:
        return "⚡ STATE: CREATIVE SURGE (High Energy!)", "\033[91m" # Red
        
    else:
        return "🔄 STATE: CALIBRATING...", "\033[90m" # Grey

# Run Optical Nerve (C++)
process = subprocess.Popen(
    [EXE_PATH],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

print("🔗 [LINKED] OPTICAL NERVE ATTACHED. AWAITING INPUT...\n")

try:
    while True:
        line = process.stdout.readline()
        if not line: break
        
        line = line.strip()
        if line.startswith("FLUX:"):
            try:
                # 1. Receive Raw Data
                raw_flux = int(line.split(":")[1])
                
                # 2. Store in Memory
                flux_memory.append(raw_flux)
                
                # 3. Analyze Mental Pattern
                intent, color = analyze_pattern(flux_memory)
                
                # 4. Visual Display
                bar = "█" * int(raw_flux / 2)
                padding = " " * (40 - len(bar))
                
                # Interactive Print
                sys.stdout.write(f"\r{color}BIO-SIGNAL: |{bar}{padding}| {raw_flux:03d} >> {intent}\033[0m")
                sys.stdout.flush()
                
            except ValueError:
                pass

except KeyboardInterrupt:
    print("\n\n🛑 HERMES SHUTDOWN.")
    process.terminate()
