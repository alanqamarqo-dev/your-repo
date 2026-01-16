import subprocess
import sys
import os
import time
import collections
import threading

# ==============================================================================
# AGL HERMES: THE FULL STACK (Vision + Brain + Voice)
# ==============================================================================

# Use absolute path to ensure we find the exe
current_dir = os.path.dirname(os.path.abspath(__file__))
EXE_PATH = os.path.join(current_dir, "agl_camera.exe")
MEMORY_SIZE = 20

print("🤖 [HERMES] INITIALIZING FULL SYSTEM (VISION + BRAIN + VOICE)...")

if not os.path.exists(EXE_PATH):
    print(f"❌ Error: agl_camera.exe not found at {EXE_PATH}")
    sys.exit()

flux_memory = collections.deque(maxlen=MEMORY_SIZE)
last_spoken_state = "NONE" # To avoid repeating speech

# --- Voice Engine (No External Libraries) ---
def speak_worker(phrase):
    """
    Uses PowerShell to speak, avoiding the need for external libraries.
    """
    # PowerShell command to access .NET Speech library
    ps_command = f'Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{phrase}");'
    
    # Run command in background (Hidden window)
    subprocess.run(["powershell", "-Command", ps_command], creationflags=subprocess.CREATE_NO_WINDOW)

def speak(phrase):
    # Run speech in a separate thread to not block video processing
    t = threading.Thread(target=speak_worker, args=(phrase,))
    t.daemon = True
    t.start()

# --- Brain Logic ---
def analyze_pattern(memory):
    if len(memory) < MEMORY_SIZE: return "INIT", "WHITE", None
    
    avg_flux = sum(memory) / len(memory)
    
    # Calibrated Logic
    if avg_flux < 1.0:
        return "DEEP THOUGHT", "\033[94m", "Silence detected. Aligning with your thoughts."
    
    elif 1.0 <= avg_flux < 8.0:
        return "FOCUSED WORK", "\033[92m", "Systems active. I am following your lead."
        
    elif avg_flux >= 8.0:
        return "CREATIVE SURGE", "\033[91m", "Energy spike detected! Channeling power."
        
    else:
        return "CALIBRATING", "\033[90m", None

# --- Main Loop ---
process = subprocess.Popen(
    [EXE_PATH],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

print("🔗 [LINKED] ALL SYSTEMS ONLINE.\n")

try:
    while True:
        line = process.stdout.readline()
        if not line: break
        
        line = line.strip()
        if line.startswith("FLUX:"):
            try:
                raw_flux = int(line.split(":")[1])
                flux_memory.append(raw_flux)
                
                # 1. Analyze State
                state_name, color, voice_phrase = analyze_pattern(flux_memory)
                
                # 2. Speech Decision (Only if state changes)
                if state_name != last_spoken_state and state_name != "INIT":
                    if voice_phrase:
                        speak(voice_phrase) # 🗣️ Speak!
                    last_spoken_state = state_name
                
                # 3. Visual Display
                bar = "█" * int(raw_flux / 2)
                padding = " " * (40 - len(bar))
                sys.stdout.write(f"\r{color}HERMES: |{bar}{padding}| {raw_flux:03d} >> {state_name}   \033[0m")
                sys.stdout.flush()
                
            except ValueError:
                pass

except KeyboardInterrupt:
    print("\n\n🛑 HERMES SHUTDOWN.")
    process.terminate()
