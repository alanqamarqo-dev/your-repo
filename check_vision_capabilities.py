import sys
import importlib.util

def check_library(name, pip_name=None):
    if pip_name is None:
        pip_name = name
    
    spec = importlib.util.find_spec(name)
    if spec is not None:
        print(f"[OK] {pip_name} ({name}) is installed.")
        try:
            lib = importlib.import_module(name)
            if hasattr(lib, '__version__'):
                print(f"     Version: {lib.__version__}")
        except Exception as e:
            print(f"     Error importing: {e}")
        return True
    else:
        print(f"[MISSING] {pip_name} ({name}) is NOT found.")
        return False

print("--- AGL Vision Capability Check ---")
print(f"Python Interpreter: {sys.executable}")
print(f"Python Version: {sys.version}")
print("-" * 30)

has_cv2 = check_library("cv2", "opencv-python")
has_pil = check_library("PIL", "Pillow")
has_skimage = check_library("skimage", "scikit-image")
has_imageio = check_library("imageio", "imageio")
has_matplotlib = check_library("matplotlib", "matplotlib")

print("-" * 30)
if has_cv2:
    print("RESULT: Real Camera Vision is POSSIBLE.")
elif has_pil or has_imageio:
    print("RESULT: Static/File-based Vision is POSSIBLE (No Webcam).")
else:
    print("RESULT: Only Simulation Mode is available.")
