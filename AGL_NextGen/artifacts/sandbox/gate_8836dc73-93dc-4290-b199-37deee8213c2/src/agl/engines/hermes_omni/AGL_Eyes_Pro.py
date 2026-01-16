import ctypes
import os
import random
import math
import time

# Try to import OpenCV and NumPy, but don't crash if missing
try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    print("⚠️ [AGL_PRO] OpenCV/NumPy not found. Running in Hardware-Less Mode.")

class AGL_Eyes_Pro:
    def __init__(self):
        print("👁️ [AGL_PRO] Initializing Professional Vision System...")
        self.dll_path = os.path.join(os.path.dirname(__file__), "agl_core.dll")
        self.use_dll = False
        self.camera_active = False
        self.cap = None

        # 1. Try to open Camera (if libraries exist)
        if HAS_OPENCV:
            try:
                self.cap = cv2.VideoCapture(0)
                if self.cap.isOpened():
                    self.camera_active = True
                    print("✅ [AGL_PRO] Camera Hardware Active.")
                else:
                    print("⚠️ [AGL_PRO] Camera not found. Switching to Simulation Mode.")
            except Exception as e:
                print(f"⚠️ [AGL_PRO] Camera Error: {e}")
        else:
            print("⚠️ [AGL_PRO] Vision Libraries Missing. Using Synthetic Bio-Flux.")

        # 2. Load C++ Library (The Core Engine)
        if os.path.exists(self.dll_path):
            try:
                self.lib = ctypes.CDLL(self.dll_path)
                
                # Define function signature:
                # float process_frame_data(unsigned char* data, int size, int width, int height)
                self.lib.process_frame_data.argtypes = [
                    ctypes.POINTER(ctypes.c_ubyte), # data pointer
                    ctypes.c_int,                   # size
                    ctypes.c_int,                   # width
                    ctypes.c_int                    # height
                ]
                self.lib.process_frame_data.restype = ctypes.c_float
                
                # Check status if function exists
                if hasattr(self.lib, 'get_core_status'):
                    if self.lib.get_core_status() == 1:
                        print("✅ [AGL_PRO] C++ Processing Core Loaded (High Performance).")
                        self.use_dll = True
                else:
                    # Fallback if get_core_status isn't exported, assume it works if loaded
                    print("✅ [AGL_PRO] C++ Processing Core Loaded.")
                    self.use_dll = True
                    
            except Exception as e:
                print(f"⚠️ [AGL_PRO] Failed to load DLL: {e}")
        else:
            print("⚠️ [AGL_PRO] 'agl_core.dll' not found. Using Python Processing.")

        self.internal_energy = 1.0
        
        # Pre-allocate a dummy buffer for simulation mode to avoid re-allocating every frame
        self.sim_width = 640
        self.sim_height = 480
        self.sim_size = self.sim_width * self.sim_height
        self.sim_buffer = (ctypes.c_ubyte * self.sim_size)()

    def scan(self, sensitivity=10):
        """
        Hybrid Scan: 
        - If Camera: Python grabs frame -> C++ processes it.
        - If No Camera: Python generates noise -> C++ processes it.
        """
        if self.camera_active and HAS_OPENCV:
            ret, frame = self.cap.read()
            if not ret: return 0.0
            
            # Convert to Grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if self.use_dll:
                # --- Fast Path (C++) ---
                height, width = gray.shape
                # Get pointer to numpy array data
                data_ptr = gray.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
                size = height * width
                
                # Send to C++
                raw_energy = self.lib.process_frame_data(data_ptr, size, width, height)
                return raw_energy * (sensitivity / 5.0)
            else:
                # --- Slow Path (Python) ---
                std_dev = np.std(gray)
                return (std_dev / 10.0) * (sensitivity / 5.0)
                
        else:
            # --- Simulation Mode (Synthetic Vision) ---
            # Even in simulation, we can use the C++ engine to process "static"
            
            if self.use_dll:
                # Fill buffer with random noise (simulating visual static)
                # For speed, we won't fill every byte every frame in python (too slow),
                # we'll just randomize a few or rely on the C++ engine reading the buffer.
                # Let's just pass the buffer. In a real app, we'd fill it.
                # To make it "alive", let's modify the first few bytes based on internal energy
                
                # Simple "Heartbeat" in the data
                val = int((math.sin(self.internal_energy) + 1) * 127)
                self.sim_buffer[0] = val
                self.sim_buffer[100] = 255 - val
                
                data_ptr = ctypes.cast(self.sim_buffer, ctypes.POINTER(ctypes.c_ubyte))
                
                # C++ calculates entropy of this buffer
                raw_energy = self.lib.process_frame_data(data_ptr, self.sim_size, self.sim_width, self.sim_height)
                
                self.internal_energy += 0.1
                return raw_energy * (sensitivity / 5.0) + (math.sin(self.internal_energy)*2)
            
            else:
                # Pure Python Simulation
                noise = random.random()
                raw_signal = math.sin(self.internal_energy) * math.cos(self.internal_energy * 0.5)
                self.internal_energy += 0.1
                result = (raw_signal * sensitivity) + noise
                return abs(result)

    def get_status_label(self, flux):
        if flux < 3.0: return "ZEN (Stable)"
        if flux > 8.0: return "CHAOS (Critical)"
        return "ACTIVE (Normal)"
        
    def close(self):
        if self.camera_active and self.cap:
            self.cap.release()
