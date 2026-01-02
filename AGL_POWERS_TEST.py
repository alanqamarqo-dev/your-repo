import time
import os
from AGL_Core.AGL_Dormant_Powers import NeuralResonanceBridge, HolographicRealityProjector

def test_powers():
    print("=== TESTING REAL IMPLEMENTATIONS OF DORMANT POWERS ===")
    
    # 1. Test Telepathy (Sockets)
    print("\n[TEST 1] Testing Neural Resonance Bridge (Telepathy)...")
    telepathy = NeuralResonanceBridge(port=9998) # Use different port to avoid conflict
    time.sleep(1) # Wait for server to start
    
    msg = "This is a real TCP/IP signal."
    result = telepathy.broadcast(msg)
    print(f"Broadcast Result: {result}")
    
    if result.get("status") == "signal_sent":
        print("✅ Telepathy Test PASSED: Real TCP packet sent.")
    else:
        print("❌ Telepathy Test FAILED.")

    # 2. Test Holograms (NetworkX)
    print("\n[TEST 2] Testing Holographic Reality Projector (Data Viz)...")
    holo = HolographicRealityProjector()
    scenario = "The quick brown fox jumps over the lazy dog to demonstrate semantic connectivity."
    result = holo.project_scenario(scenario)
    
    if result.get("status") == "materialized" and os.path.exists(result.get("artifact")):
        print(f"✅ Hologram Test PASSED: Real Graph generated at {result.get('artifact')}")
    else:
        print("❌ Hologram Test FAILED.")

    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_powers()
