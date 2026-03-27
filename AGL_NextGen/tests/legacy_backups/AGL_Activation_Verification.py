"""
AGL_Activation_Verification.py
Verifies that high-level super intelligence capabilities are auto-activated.
"""
import sys
import os

# Setup Path
sys.path.insert(0, os.path.join(os.getcwd(), 'AGL_NextGen', 'src'))
sys.path.insert(0, os.path.join(os.getcwd(), 'repo-copy', 'Engineering_Engines'))

from agl.core.super_intelligence import AGL_Super_Intelligence

print("--- STARTING VERIFICATION ---")
si = AGL_Super_Intelligence()
print("--- END VERIFICATION ---")
