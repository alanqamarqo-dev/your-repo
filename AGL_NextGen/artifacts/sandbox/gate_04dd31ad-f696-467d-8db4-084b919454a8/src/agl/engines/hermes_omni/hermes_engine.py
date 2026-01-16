import os
import subprocess
import collections
import threading
import time

class HermesOmniEngine:
    """
    Hermes Omni Engine - Vision, Brain, and Voice Integration.
    Wraps the C++ Camera executable and Python logic.
    """
    def __init__(self, memory_size=20):
        self.memory_size = memory_size
        self.flux_memory = collections.deque(maxlen=memory_size)
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.exe_path = os.path.join(self.current_dir, "agl_camera.exe")
        self.process = None
        self.running = False
        self.thread = None

    def start(self):
        """Starts the Hermes Engine (Camera + Analysis Loop) in a background thread."""
        if not os.path.exists(self.exe_path):
            print(f"⚠️ [HERMES] Camera executable not found at {self.exe_path}")
            return

        print("🤖 [HERMES] Starting Neural Interpreter...")
        self.running = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stops the Hermes Engine."""
        self.running = False
        if self.process:
            self.process.terminate()
        if self.thread:
            self.thread.join(timeout=1.0)
        print("🤖 [HERMES] Stopped.")

    def _run_loop(self):
        try:
            self.process = subprocess.Popen(
                [self.exe_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            while self.running and self.process.poll() is None:
                line = self.process.stdout.readline()
                if not line:
                    break
                
                try:
                    flux_val = float(line.strip())
                    self.flux_memory.append(flux_val)
                    state, color = self.analyze_pattern()
                    # In a real engine, we might log this or broadcast an event
                    # print(f"{color}{state}\033[0m") 
                except ValueError:
                    pass
        except Exception as e:
            print(f"❌ [HERMES] Error in loop: {e}")
        finally:
            if self.process:
                self.process.terminate()

    def analyze_pattern(self):
        if len(self.flux_memory) < self.memory_size:
            return "INITIALIZING...", "WHITE"
        
        avg_flux = sum(self.flux_memory) / len(self.flux_memory)
        
        if avg_flux < 1.0:
            return "🌌 STATE: DEEP THOUGHT (System Idle)", "\033[94m"
        elif 1.0 <= avg_flux < 8.0:
            return "👁️ STATE: FOCUSED WORK (Active)", "\033[92m"
        elif avg_flux >= 8.0:
            return "⚡ STATE: CREATIVE SURGE (High Energy!)", "\033[91m"
        else:
            return "🔄 STATE: CALIBRATING...", "\033[90m"
