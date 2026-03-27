import sys
import os
import json
import time

# Setup Path
sys.path.insert(0, os.path.join(os.getcwd(), 'AGL_NextGen', 'src'))

print("🧪 STARTING AGL ABSTRACTION & SELF-FORGING VERIFICATION TEST...")

# 1. Test Metaphysics (Abstract Concept Synthesis)
try:
    print("\n[1] Testing Abstract Concept Forging (Metaphysics)...")
    from agl.engines.metaphysics import HeikalMetaphysicsEngine
    meta = HeikalMetaphysicsEngine()
    # Create a new concept "Bittersweet" from Joy and Sadness
    components = {"joy": 0.6, "sadness": 0.4}
    result = meta.synthesize_concept("Bittersweet_Test", components)
    print(f"   ✅ Result: {result}")
    dist = meta.get_concept_distance("joy", "Bittersweet_Test")
    print(f"   ✅ Distance to Joy: {dist:.4f}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

# 2. Test Simulation (Internal Emulation Loop)
try:
    print("\n[2] Testing Internal Emulation Loop (Simulation)...")
    from agl.engines.advanced_simulation import AdvancedSimulationEngine
    sim = AdvancedSimulationEngine()
    payload = {
        "mode": "internal_emulation",
        "variables": {"entropy": 10.0, "clarity": 0.0},
        "steps": 10
    }
    res = sim.process_task(payload)
    if res.get("mode") == "internal_emulation":
        print(f"   ✅ Emulation Successful. Final Clarity: {res.get('final_clarity'):.4f}")
        print(f"   ✅ Thought Log: {json.dumps(res.get('thought_process'), indent=2)}")
    else:
        print(f"   ❌ Failed: Mode mismatch or old engine version.")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

# 3. Test Causal Graph (Abstract Merge)
try:
    print("\n[3] Testing Multimodal Abstraction (Causal Graph)...")
    from agl.engines.causal_graph import CausalGraphEngine
    causal = CausalGraphEngine()
    c1 = {"name": "Wheel", "properties": ["round", "rolls", "cycle"]}
    c2 = {"name": "Day", "properties": ["light", "dark", "cycle"]}
    res = causal.abstract_merge(c1, c2)
    print(f"   ✅ Result: {json.dumps(res, indent=2)}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

# 4. Test Recursive Improver (Tool Forging)
try:
    print("\n[4] Testing Tool Forging (Recursive Improver)...")
    from agl.engines.recursive_improver import RecursiveImprover
    improver = RecursiveImprover()
    
    # Mock Consent for Test (We mock the method to valid true for this test only)
    improver._check_human_consent = lambda: True 
    print("   ℹ️ (Mocked Consent to TRUE for verification)")

    tool_code = """
def hello_world():
    return "Hello from the Forged Tool!"
"""
    res = improver.forge_new_tool("Test_Tool_Alpha", tool_code)
    print(f"   ✅ Result: {res}")
    
    if res.get('ok'):
        # Verify import works (The engine does hot load, but let's check usage)
        # Note: The engine loads it as 'agl.engines.gen_test_tool_alpha'
        import sys
        # We need to construct the module name based on what we passed
        mod_name = "agl.engines.gen_test_tool_alpha" 
        if mod_name in sys.modules:
             gen_tool = sys.modules[mod_name]
             print(f"   ✅ Execution Verify: {gen_tool.hello_world()}")
        else:
             print("   ⚠️ Module not in sys.modules, trying manual import...")
             # It might need explicit import if hot load logic in engine had issues
             try:
                 import agl.engines.gen_test_tool_alpha as gen_tool # type: ignore
                 print(f"   ✅ Execution Verify: {gen_tool.hello_world()}")
             except ImportError:
                 print("   ❌ Import verification failed.")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

print("\n✅ VERIFICATION COMPLETE.")