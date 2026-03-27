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
        import random
        try:
            self.process = subprocess.Popen(
                [self.exe_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            while self.running:
                # Check if process is dead
                if self.process.poll() is not None:
                    # Process died (no camera?), switch to simulation
                    self._simulate_vision()
                    time.sleep(0.1)
                    continue

                line = self.process.stdout.readline()
                if not line:
                    # No output currently available or EOF
                    if self.process.poll() is not None:
                        continue
                    # Check if we are starving for data (Blindness check)
                    # For now, just continue, the loop will retry
                    continue
                
                # Protocol Fix: Handle VEC:x,y
                line = line.strip()
                flux_val = 0.0
                
                if line.startswith("VEC:"):
                    parts = line.split(":")
                    if len(parts) > 1:
                        coords = parts[1]
                        if coords == "NONE":
                            flux_val = 0.5 # Low noise
                        else:
                            try:
                                if "," in coords:
                                    cx, cy = map(int, coords.split(","))
                                    # Calculate conceptual 'flux' from motion vector
                                    # 160, 120 is center. Deviation implies activity.
                                    flux_val = (abs(cx - 160) + abs(cy - 120)) / 10.0 + 2.0
                                    # Cap reasonable max
                                    if flux_val > 20.0: flux_val = 20.0
                            except:
                                flux_val = 0.0
                    self.flux_memory.append(flux_val)

                else:
                    # Legacy float support
                    try:
                        flux_val = float(line)
                        self.flux_memory.append(flux_val)
                    except ValueError:
                        # Garbage or debug info, ignore
                        pass
                
        except Exception as e:
            print(f"❌ [HERMES] Error in loop: {e}")
            # Fallback to internal simulation if driver crashes
            while self.running:
                self._simulate_vision()
                time.sleep(0.1)
                
        finally:
            if self.process:
                self.process.terminate()

    def _simulate_vision(self):
        import random
        # Simulates 'Mind's Eye' when hardware is offline
        # Generates a wave-like pattern
        base = 4.0
        noise = random.uniform(-2.0, 5.0)
        self.flux_memory.append(base + noise)

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
