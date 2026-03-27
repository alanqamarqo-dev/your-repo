import subprocess
import time
import os
import sys
import threading

print("👁️ [HERMES] INITIALIZING C++ OPTICAL SUBSYSTEM...")

# Use absolute path to ensure we find the exe
current_dir = os.path.dirname(os.path.abspath(__file__))
exe_path = os.path.join(current_dir, "agl_camera.exe")

if not os.path.exists(exe_path):
    print(f"❌ ERROR: {exe_path} not found!")
    print("   -> Did you run the compile command?")
    print("   -> g++ agl_camera.cpp -o agl_camera.exe -lvfw32")
    sys.exit()

def read_output(process):
    """Reads stdout from the C++ process and visualizes the flux."""
    try:
        for line in iter(process.stdout.readline, b''):
            line_str = line.decode('utf-8').strip()
            if line_str.startswith("FLUX:"):
                try:
                    flux_val = int(line_str.split(":")[1])
                    
                    # Create a visual bar
                    bar_length = 50
                    filled_length = int(bar_length * flux_val // 100)
                    bar = '█' * filled_length + '-' * (bar_length - filled_length)
                    
                    # Color coding (ANSI escape codes)
                    color = "\033[92m" # Green
                    if flux_val > 30: color = "\033[93m" # Yellow
                    if flux_val > 70: color = "\033[91m" # Red
                    reset = "\033[0m"
                    
                    sys.stdout.write(f"\r{color}⚡ FLUX: [{bar}] {flux_val}%{reset}")
                    sys.stdout.flush()
                except ValueError:
                    pass
    except Exception as e:
        pass

try:
    print("🚀 [KERNEL] Injecting Heikal Optical Core...")
    time.sleep(1)
    
    # Run C++ program with piped stdout
    process = subprocess.Popen(exe_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    print("✅ [ONLINE] Visual Cortex is Active.")
    print("   -> Algorithm: Heikal Porosity Filter + Resonance")
    print("   -> Press Ctrl+C to terminate the link.")
    print("")

    # Start a thread to read output so we don't block
    reader_thread = threading.Thread(target=read_output, args=(process,))
    reader_thread.daemon = True
    reader_thread.start()
    
    # Keep main thread alive
    while True:
        if process.poll() is not None:
            print("\n⚠️ Camera Module Disconnected externally.")
            break
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n\n🛑 Terminating Subsystem...")
    process.terminate()
