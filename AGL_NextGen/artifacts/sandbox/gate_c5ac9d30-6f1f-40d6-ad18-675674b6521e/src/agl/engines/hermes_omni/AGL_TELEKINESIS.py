import subprocess
import sys
import os
import ctypes
import time

# ==============================================================================
# AGL TELEKINESIS PROTOCOL (No External Libs)
# ==============================================================================

# Use absolute path to ensure we find the exe
current_dir = os.path.dirname(os.path.abspath(__file__))
EXE_PATH = os.path.join(current_dir, "agl_camera.exe")

# 1. Windows Definitions for Mouse/Keyboard Control (Low Level)
user32 = ctypes.windll.user32
screen_width = user32.GetSystemMetrics(0)
screen_height = user32.GetSystemMetrics(1)

# Camera Constants (Must match C++)
CAM_W = 320
CAM_H = 240

# Physics Smoothing
last_mouse_x, last_mouse_y = screen_width // 2, screen_height // 2
SMOOTH_FACTOR = 0.2

# Gesture Detection
gesture_history = []
last_code_time = 0

def move_mouse(cam_x, cam_y):
    global last_mouse_x, last_mouse_y
    
    # Map camera coordinates to screen
    target_x = int((cam_x / CAM_W) * screen_width)
    target_y = int((cam_y / CAM_H) * screen_height)
    
    # Apply Physics Smoothing
    new_x = int(last_mouse_x + (target_x - last_mouse_x) * SMOOTH_FACTOR)
    new_y = int(last_mouse_y + (target_y - last_mouse_y) * SMOOTH_FACTOR)
    
    user32.SetCursorPos(new_x, new_y)
    last_mouse_x, last_mouse_y = new_x, new_y
    return new_y # Return Y for gesture detection

def type_code_snippet():
    """Auto-type Python code upon gesture."""
    code = """
    # AGL GENERATED CODE
    def neural_link():
        print("System Connected via Hermes Link.")
        return True
    """
    # Simulating typing is complex with pure ctypes without a helper function for every key.
    # For this demo, we will print to console to prove the intent was caught.
    # In a full version, we would use keybd_event for each char.
    
    print("\n⚡ [HERMES] NOD DETECTED -> WRITING CODE SNIPPET...")
    print(code)

def detect_nod(y_pos):
    global last_code_time
    current_time = time.time()
    
    # Debounce
    if current_time - last_code_time < 2.0: return

    gesture_history.append((y_pos, current_time))
    if len(gesture_history) > 10: gesture_history.pop(0)
    
    # Analyze Motion: Down then Up quickly?
    if len(gesture_history) >= 5:
        y_values = [p[0] for p in gesture_history]
        min_y = min(y_values)
        max_y = max(y_values)
        
        # If vertical movement is significant
        if (max_y - min_y) > 50:
            # Check pattern: Middle -> Down -> Up (Simplified)
            type_code_snippet()
            last_code_time = current_time
            gesture_history.clear()

# --- Main Loop ---
print("🖱️ [TELEKINESIS] INITIALIZING MIND-MOUSE LINK...")
print("   -> Move your head to move the mouse.")
print("   -> NOD quickly to write code.")

if not os.path.exists(EXE_PATH):
    print(f"❌ Error: agl_camera.exe not found at {EXE_PATH}")
    sys.exit()

process = subprocess.Popen([EXE_PATH], stdout=subprocess.PIPE, text=True, bufsize=1)

try:
    while True:
        line = process.stdout.readline()
        if not line: break
        
        line = line.strip()
        if line.startswith("VEC:"):
            data = line.split(":")[1]
            
            if data == "NONE":
                continue
                
            try:
                x, y = map(int, data.split(","))
                
                # 1. Move Mouse
                curr_y = move_mouse(x, y)
                
                # 2. Detect Gesture
                detect_nod(curr_y)
                
            except ValueError:
                pass

except KeyboardInterrupt:
    process.terminate()
