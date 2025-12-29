import sys
import os
import importlib
import time

# إعداد المسارات
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

def check_pulse(module_name, description):
    print(f"🩺 Checking {description} ({module_name})...", end=" ")
    try:
        importlib.import_module(module_name)
        print("✅ ALIVE")
        return True
    except ImportError as e:
        print(f"❌ CRITICAL FAILURE: {e}")
        return False
    except Exception as e:
        print(f"⚠️ WARNING: {e}")
        return False

print("\n🏥 AGL SYSTEM HEALTH CHECK PROTOCOL")
print("===================================")
print(f"📂 Root Directory: {root_dir}")

all_systems_go = True

# 1. فحص العقل المدبر (Core)
all_systems_go &= check_pulse("AGL_Core.AGL_Awakened", "The Awakened Mind")
all_systems_go &= check_pulse("AGL_Core.Heikal_Quantum_Core", "The Observer (Quantum Core)")

# 2. فحص المحركات (Engines)
all_systems_go &= check_pulse("AGL_Engines.Volition_Engine", "Free Will (Volition)")
all_systems_go &= check_pulse("AGL_Engines.HiveMind", "Collective Intelligence (Hive Mind)")
all_systems_go &= check_pulse("AGL_Engines.Mathematical_Brain", "Logic Center (Math Brain)")

# 3. فحص الذاكرة (Memory)
all_systems_go &= check_pulse("AGL_Memory.Holographic_LLM", "Long-Term Memory")

# 4. فحص المحاكاة (Simulations)
all_systems_go &= check_pulse("AGL_Simulations.AGL_Genesis_Simulator", "Genesis Simulator")

print("===================================")
if all_systems_go:
    print("✨ SYSTEM STATUS: GREEN. The transplant was successful.")
    print("🚀 READY FOR AUTONOMY.")
else:
    print("🚨 SYSTEM STATUS: RED. Immediate intervention required.")
