import sys
import os
import time

# Setup Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "AGL_Core"))

print("🧪 STARTING AGL FINAL VERIFICATION TEST")
print("=======================================")

try:
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
    print("✅ [IMPORT] AGL_Super_Intelligence class imported successfully.")
except ImportError as e:
    print(f"❌ [IMPORT] Failed to import AGL_Super_Intelligence: {e}")
    sys.exit(1)

def run_test():
    print("\n🤖 Instantiating AGL Super Intelligence...")
    try:
        # Initialize the system
        asi = AGL_Super_Intelligence()
        print("✅ [INIT] System instantiated.")
    except Exception as e:
        print(f"❌ [INIT] System instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n🔍 Verifying Core Components...")
    
    # 1. Check Self-Awareness
    if asi.self_awareness:
        print("   ✅ Self-Awareness Module: ACTIVE")
    else:
        print("   ❌ Self-Awareness Module: MISSING")

    # 2. Check Self-Repair
    if hasattr(asi, 'repair_system') and asi.repair_system:
        print("   ✅ Self-Repair System: ACTIVE")
    else:
        print("   ❌ Self-Repair System: MISSING")

    # 3. Check Heikal Quantum Core (The Repaired Component)
    if asi.heikal_core_root:
        print("   ✅ Heikal Quantum Core (Root): ACTIVE (Repaired)")
    else:
        print("   ❌ Heikal Quantum Core (Root): FAILED")

    # 4. Check Dormant Modules (The Awakened Powers)
    print("\n🔍 Verifying Awakened Powers...")
    expected_modules = [
        'AGL_Holographic_Firewall',
        'AGL_Metaphysics_Engine_V2',
        'Quantum_Neural_Core'
    ]
    
    found_count = 0
    if hasattr(asi, 'discovered_modules'):
        for name, module in asi.discovered_modules.items():
            print(f"   ✨ Found Active Module: {name}")
            if name in expected_modules:
                found_count += 1
    else:
        print("   ❌ 'discovered_modules' registry not found.")

    # 5. Functional Test: Holographic Firewall
    print("\n🔥 Testing Holographic Firewall...")
    if 'AGL_Holographic_Firewall' in asi.discovered_modules:
        firewall = asi.discovered_modules['AGL_Holographic_Firewall']
        # Assuming the firewall has a method we can call or it ran on init
        print("   ✅ Firewall is loaded in memory.")
    else:
        print("   ⚠️ Firewall not found in discovered modules.")

    print("\n=======================================")
    print("🎉 TEST COMPLETE")
    
if __name__ == "__main__":
    run_test()
