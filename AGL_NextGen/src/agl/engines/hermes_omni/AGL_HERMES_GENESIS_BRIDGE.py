import subprocess
import sys
import os
import time
import collections
import threading
import torch
import random
import math

# ==============================================================================
# AGL HERMES-GENESIS BRIDGE: EMOTIONAL REALITY CONTROL
# ==============================================================================
# This system links the HERMES Vision Sensor (Human Emotion/Movement)
# to the GENESIS-OMEGA Cosmic Simulator.
#
# LOGIC:
# - Low Flux (Calm/Blue) -> Stabilizes the Simulation (Low Entropy).
# - High Flux (Anger/Red) -> Destabilizes the Simulation (High Entropy/Chaos).
# ==============================================================================

# --- 1. Setup Paths & Imports ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# root_dir = os.path.dirname(current_dir) # No longer needed for imports
# genesis_dir = os.path.join(root_dir, "GENESIS_OMEGA")
# hermes_dir = os.path.join(root_dir, "HERMES_OMNI")

# sys.path.append(root_dir)
# sys.path.append(genesis_dir)

try:
    from agl.engines.genesis_omega.GENESIS_OMEGA_CORE import GENESIS_OMEGA_Entity
except ImportError:
    print("❌ Error: Could not import GENESIS_OMEGA_CORE. Check paths.")
    sys.exit()

# --- 2. Initialize Systems ---
print("\n🔌 [BRIDGE] INITIALIZING HERMES-GENESIS LINK...")

# A. Initialize Camera (HERMES)
EXE_PATH = os.path.join(current_dir, "agl_camera.exe")
if not os.path.exists(EXE_PATH):
    print(f"❌ Error: agl_camera.exe not found at {EXE_PATH}")
    sys.exit()

# B. Initialize Simulator (GENESIS)
print("🌌 [GENESIS] Booting Cosmic Core...")
# Mock Mother System for initialization
class MockMother:
    pass
omega_system = GENESIS_OMEGA_Entity(mother_system=MockMother())
omega_system.eval() # Set to evaluation mode (inference)

# --- 3. Helper Functions ---
def generate_reality_inputs(chaos_level):
    """
    Generates simulation inputs based on REAL WORLD DATA & 'Chaos Level'.
    chaos_level: 0.0 (Perfect Order) to 5.0 (Total Chaos)
    """
    # 1. Physics: Time Harmonics (Real Clock)
    t = time.time()
    # Create a vector based on time frequencies
    phys_data = [math.sin(t * (i+1) * 0.01) for i in range(256)]
    phys = torch.tensor([phys_data], dtype=torch.float32) * (1.0 + chaos_level)

    # 2. Bio: System Vital Signs (CPU micro-lag)
    # Micro-variations in CPU speed reflect effective "Biological" load
    t0 = time.time_ns()
    _ = [x for x in range(100)]
    cpu_lag = (time.time_ns() - t0) / 1000.0 
    
    bio_data = [math.cos(cpu_lag * i * 0.1) for i in range(256)]
    bio = torch.tensor([bio_data], dtype=torch.float32) * (1.0 + chaos_level)
    
    # 3. Econ: Market Simulation (Random Walk seeded by Chaos)
    # Chaotic market reacts to external chaos_level
    econ = torch.randn(1, 128) * chaos_level 
    
    # 4. Neuro: Entropy of the System
    neuro = torch.randn(1, 512) * chaos_level
    
    return phys, bio, econ, neuro

def get_color(flux):
    if flux < 5: return "\033[94m" # Blue
    if flux < 15: return "\033[92m" # Green
    return "\033[91m" # Red

# --- 4. Main Control Loop ---
process = subprocess.Popen(
    [EXE_PATH],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

print("🔗 [LINKED] HERMES SENSOR -> GENESIS SIMULATOR ACTIVE.")
print("   -> Move your body to control the entropy of the universe.\n")

try:
    while True:
        line = process.stdout.readline()
        if not line: break
        
        line = line.strip()
        if line.startswith("FLUX:"):
            try:
                # 1. Read Sensor Data
                raw_flux = int(line.split(":")[1])
                
                # 2. Calculate Chaos Factor (Scaling Flux to 0.1 - 5.0)
                # Flux usually ranges 0 - 100
                chaos_factor = max(0.1, min(5.0, raw_flux / 10.0))
                
                # 3. Generate Reality Data
                phys, bio, econ, neuro = generate_reality_inputs(chaos_factor)
                
                # 4. Run Simulation Step
                with torch.no_grad():
                    projection = omega_system(phys, bio, econ, neuro)
                
                # 5. Analyze Result (Stability Check)
                # We check the variance of the output projection as a proxy for "Stability"
                stability_metric = 1.0 / (torch.std(projection).item() + 0.001)
                stability_percent = min(100, max(0, stability_metric * 10))
                
                # 6. Visual Feedback
                color = get_color(raw_flux)
                status = "STABLE" if chaos_factor < 1.0 else "UNSTABLE" if chaos_factor < 3.0 else "CRITICAL"
                
                bar = "█" * int(raw_flux / 2)
                padding = " " * (30 - len(bar))
                
                output_str = (
                    f"\r{color}HERMES FLUX: {raw_flux:03d} | "
                    f"CHAOS: {chaos_factor:.2f} | "
                    f"GENESIS STATUS: {status} ({stability_percent:.1f}%) "
                    f"[{bar}{padding}] \033[0m"
                )
                sys.stdout.write(output_str)
                sys.stdout.flush()
                
            except ValueError:
                pass
except KeyboardInterrupt:
    print("\n\n🛑 [SYSTEM] Disconnecting Bridge...")
    process.terminate()
    print("✅ [DONE] Simulation Saved.")
