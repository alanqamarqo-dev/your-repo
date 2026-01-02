import sys
import os
import importlib

sys.path.append(os.getcwd())

try:
    mod = importlib.import_module("AGL_Core.Heikal_Quantum_Core")
    print(f"Module loaded: {mod}")
    print(f"File: {mod.__file__}")
    if hasattr(mod, "HeikalQuantumCore"):
        print("Class HeikalQuantumCore FOUND.")
    else:
        print("Class HeikalQuantumCore NOT FOUND.")
        print("Dir:", dir(mod))
except Exception as e:
    print(f"Import failed: {e}")
