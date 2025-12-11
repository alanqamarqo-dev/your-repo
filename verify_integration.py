"""
🔍 Verify Memory & Consciousness Integration
==========================================

This script verifies that ALL memory and consciousness systems
are properly integrated into UnifiedAGISystem.

التحقق من أن جميع أنظمة الذاكرة والوعي مرتبطة بالنظام الموحد
"""

import sys
import os

# Add repo-copy to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'repo-copy'))

print("="*60)
print("🔍 VERIFICATION: Memory & Consciousness Integration")
print("="*60)

# Test 1: Import Check
print("\n1️⃣ Testing Imports...")
try:
    from dynamic_modules.unified_agi_system import UnifiedAGISystem
    print("   ✅ UnifiedAGISystem imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import: {e}")
    sys.exit(1)

# Test 2: Instance Creation
print("\n2️⃣ Creating UnifiedAGISystem instance...")
try:
    # Import ENGINE_REGISTRY for initialization
    from Core_Engines import ENGINE_REGISTRY
    system = UnifiedAGISystem(engine_registry=ENGINE_REGISTRY)
    print("   ✅ UnifiedAGISystem instance created")
except Exception as e:
    print(f"   ❌ Failed to create instance: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Verify Memory Systems
print("\n3️⃣ Checking Memory Systems Integration...")
memory_systems = {
    'UnifiedMemorySystem': system.memory is not None,
    'ConsciousBridge': system.conscious_bridge is not None,
    'AutobiographicalMemory': system.autobiographical_memory is not None,
    'StrategicMemory': system.strategic_memory is not None,
}

for name, exists in memory_systems.items():
    status = "✅" if exists else "❌"
    print(f"   {status} {name}: {'Connected' if exists else 'Not Connected'}")

# Test 4: Verify Consciousness Systems
print("\n4️⃣ Checking Consciousness Systems Integration...")
consciousness_systems = {
    'ConsciousnessTracker': system.consciousness_tracker is not None,
    'SelfEvolution': system.self_evolution is not None,
    'TrueConsciousnessSystem': system.true_consciousness is not None,
}

for name, exists in consciousness_systems.items():
    status = "✅" if exists else "❌"
    print(f"   {status} {name}: {'Connected' if exists else 'Not Connected'}")

# Test 5: Check ConsciousBridge Details
print("\n5️⃣ ConsciousBridge Details...")
if system.conscious_bridge:
    print(f"   🌉 ConsciousBridge Status:")
    print(f"      - Enabled: {system.conscious_bridge_enabled}")
    print(f"      - STM Size: {len(system.conscious_bridge.stm)} events")
    print(f"      - LTM Size: {len(system.conscious_bridge.ltm)} events")
    if hasattr(system.conscious_bridge, 'db_path'):
        print(f"      - DB Path: {system.conscious_bridge.db_path}")
    elif hasattr(system.conscious_bridge, 'ltm') and hasattr(system.conscious_bridge.ltm, 'db_file'):
        print(f"      - DB Path: {system.conscious_bridge.ltm.db_file}")
else:
    print("   ⚠️ ConsciousBridge not initialized")

# Test 6: Check AutobiographicalMemory Details
print("\n6️⃣ AutobiographicalMemory Details...")
if system.autobiographical_memory:
    print(f"   📖 Autobiographical Memory Status:")
    print(f"      - Life Narrative: {len(system.autobiographical_memory.life_narrative)} entries")
    print(f"      - Defining Moments: {len(system.autobiographical_memory.defining_moments)} moments")
    print(f"      - Lessons Learned: {len(system.autobiographical_memory.lessons_learned)} lessons")
else:
    print("   ⚠️ AutobiographicalMemory not initialized")

# Test 7: Check Method Existence
print("\n7️⃣ Checking Integration Methods...")
methods_to_check = [
    '_initialize_conscious_bridge',
    '_initialize_consciousness_tracking',
    'process_with_full_agi'
]

for method_name in methods_to_check:
    has_method = hasattr(system, method_name)
    status = "✅" if has_method else "❌"
    print(f"   {status} {method_name}: {'Exists' if has_method else 'Missing'}")

# Final Summary
print("\n" + "="*60)
print("📊 INTEGRATION SUMMARY")
print("="*60)

total_memory = len(memory_systems)
connected_memory = sum(memory_systems.values())
total_consciousness = len(consciousness_systems)
connected_consciousness = sum(consciousness_systems.values())

print(f"\n💾 Memory Systems: {connected_memory}/{total_memory} Connected")
print(f"🧠 Consciousness Systems: {connected_consciousness}/{total_consciousness} Connected")

all_connected = (connected_memory == total_memory and 
                 connected_consciousness == total_consciousness)

if all_connected:
    print("\n🎉 ✅ ALL SYSTEMS INTEGRATED SUCCESSFULLY!")
    print("   النظام الموحد متكامل بالكامل - جميع أنظمة الذاكرة والوعي متصلة!")
else:
    print("\n⚠️ Some systems are not connected")
    print(f"   Missing Memory: {total_memory - connected_memory}")
    print(f"   Missing Consciousness: {total_consciousness - connected_consciousness}")

print("\n" + "="*60)
print("✅ Verification Complete")
print("="*60)
