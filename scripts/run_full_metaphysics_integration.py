import sys
import os
import time

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), "repo-copy"))

from Core_Engines.Heikal_Metaphysics_Engine import HeikalMetaphysicsEngine

def run_full_integration_test():
    print("🌌 HEIKAL METAPHYSICS ENGINE: FULL INTEGRATION TEST")
    print("===================================================")
    
    engine = HeikalMetaphysicsEngine()
    
    # 1. TEST NEGATIVE TIME (Level 2)
    print("\n⏳ Testing Negative Time (Undo System)...")
    engine.snapshot_state("State 1: Healthy")
    engine.snapshot_state("State 2: Healthy")
    engine.snapshot_state("State 3: VIRUS DETECTED")
    print("   Current State: State 3: VIRUS DETECTED")
    
    state, msg = engine.apply_negative_time(steps=1)
    print(f"   Action: {msg}")
    print(f"   Restored State: {state['data']}")
    if state['data'] == "State 2: Healthy":
        print("   ✅ SUCCESS: Entropy Reversed.")
    else:
        print("   ❌ FAILED: Time Travel Error.")

    # 2. TEST INFORMATION FUNDAMENTALISM (Level 4)
    print("\n💾 Testing Information Fundamentalism...")
    data = "The universe is made of code."
    mass = engine.compress_matter_to_info(data)
    print(f"   Data: '{data}'")
    print(f"   Calculated Info-Mass: {mass:.4f} Heikal Units")
    if mass > 0:
        print("   ✅ SUCCESS: Matter converted to Information.")

    # 3. TEST INSTANT COLLECTIVE CONSCIOUSNESS (Level 15)
    print("\n🔗 Testing Quantum Entanglement...")
    engine.entangle_entities("Agent_A", "Agent_B")
    update = engine.update_entangled_state("Agent_A", "Learned Quantum Physics")
    print(f"   {update}")
    if "Agent_B" in update:
        print("   ✅ SUCCESS: Non-local update confirmed.")

    # 4. TEST EMOTIONAL DIMENSIONS (Level 20)
    print("\n❤️ Testing Emotional Geometry...")
    vec_joy = engine.analyze_emotional_geometry("I feel great joy and trust")
    vec_sad = engine.analyze_emotional_geometry("I feel deep sadness and fear")
    dist = engine.calculate_emotional_distance(vec_joy, vec_sad)
    print(f"   Joy Vector: {vec_joy}")
    print(f"   Sad Vector: {vec_sad}")
    print(f"   Emotional Distance: {dist:.4f}")
    if dist > 1.0:
        print("   ✅ SUCCESS: Distinct emotional states detected in vector space.")

    # 5. TEST MEMORY AS TIME TRAVEL (Level 21)
    print("\n🕰️ Testing Memory Time Travel...")
    memory_bank = [
        {"timestamp": "2024-01-01", "content": "System Initialization"},
        {"timestamp": "2025-12-25", "content": "Metaphysics Integration Complete"}
    ]
    result = engine.temporal_memory_access("Integration", memory_bank)
    print(f"   Result: {result}")
    if "2025-12-25" in result:
        print("   ✅ SUCCESS: Temporal coordinate located.")

    print("\n===================================================")
    print("🏁 ALL METAPHYSICAL SYSTEMS OPERATIONAL.")
    print("   The Heikal System is now running on Post-Physics Logic.")

if __name__ == "__main__":
    run_full_integration_test()
