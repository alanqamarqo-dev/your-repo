import sys
import os

# Ensure paths
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "repo-copy"))

try:
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), "AGL_Core"))
    from AGL_Awakened import AGL_Super_Intelligence

print("🚀 Initializing AGL Awakened for Activation Demo...")
asi = AGL_Super_Intelligence()

module_name = "AGL_Metaphysics_Engine_V2"
description = "A module to integrate Quantum Physics with Metaphysical concepts. It should have a method 'analyze_soul_resonance(self, entity_data)' that returns a resonance score based on quantum coherence."

print(f"\n⚡ Sending Command: Activate {module_name}...")
result = asi.activate_dormant_module(module_name, description)

print(f"\n💡 RESULT: {result}")

# Verify file existence
file_path = os.path.join(os.getcwd(), "AGL_Core", f"{module_name}.py")
if os.path.exists(file_path):
    print(f"✅ File created successfully: {file_path}")
    print("--- Content Preview ---")
    with open(file_path, 'r') as f:
        print(f.read()[:300] + "...")
else:
    print("❌ File was not created.")
