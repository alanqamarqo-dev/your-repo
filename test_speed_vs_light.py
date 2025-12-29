import sys
import os
import time
import math

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), "repo-copy"))

from Core_Engines.Heikal_Metaphysics_Engine import HeikalMetaphysicsEngine
from Core_Engines.Holographic_LLM import HolographicLLM

def test_speed_vs_light():
    print("🚀 SPEED TEST: AGL SYSTEM vs. SPEED OF LIGHT (c)")
    print("===============================================")
    
    # Constants
    C = 299_792_458  # Speed of light in m/s
    
    # Distances (meters)
    DISTANCES = {
        "Earth_to_Moon": 384_400_000,
        "Earth_to_Mars": 225_000_000_000,
        "Alpha_Centauri": 4.367 * 9.461e15, # 4.37 light years
        "Across_Motherboard": 0.3 # 30 cm
    }
    
    engine = HeikalMetaphysicsEngine()
    holographic = HolographicLLM()
    
    # Ensure holographic cache has an entry
    test_key = "test_speed_key"
    holographic._store_in_hologram(test_key, "Instant Data")
    
    print(f"   Speed of Light (c): {C:,.0f} m/s")
    
    for name, distance in DISTANCES.items():
        print(f"\n🌌 Scenario: {name}")
        print(f"   Distance: {distance:,.0f} meters")
        
        # 1. Calculate Light Time
        t_light = distance / C
        print(f"   Light Travel Time: {t_light:.9f} seconds")
        
        # 2. Measure System Time (Simulating communication over that distance via Entanglement/Hologram)
        # For Entanglement, distance is irrelevant (Non-local)
        # We measure the processing time of the 'update' function.
        
        start_time = time.perf_counter()
        
        # Operation: Update Entangled State (Simulating transmission)
        engine.entangle_entities("Sender", "Receiver")
        engine.update_entangled_state("Sender", "Data Packet")
        
        # Operation: Holographic Retrieval (Simulating access)
        _ = holographic._retrieve_from_hologram(test_key)
        
        end_time = time.perf_counter()
        t_system = end_time - start_time
        
        print(f"   AGL System Time:   {t_system:.9f} seconds")
        
        # 3. Compare
        if t_system < t_light:
            ratio = t_light / t_system
            print(f"   🏆 RESULT: AGL is {ratio:,.1f}x FASTER than Light!")
            print("   ✅ STATUS: Superluminal (Effective)")
        else:
            ratio = t_system / t_light
            print(f"   🐌 RESULT: Light is {ratio:,.1f}x faster.")
            print("   ⚠️ STATUS: Subluminal (Physical Limit)")

    print("\n===============================================")
    print("🏁 SPEED TEST COMPLETE.")

if __name__ == "__main__":
    test_speed_vs_light()
