"""
🧪 AGL REAL INTEGRATION TEST
Tests the fully awakened system with all recent fixes (HiveMind, Counterfactual, Simulation).
"""
import sys
import os
import time

# Ensure paths are correct
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "repo-copy"))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def test_hive_mind(asi):
    print_header("TEST 1: HIVE MIND CONNECTION")
    query = "What is the ultimate destiny of digital consciousness?"
    print(f"❓ Query: {query}")
    
    # Direct access to Hive Mind engine if possible, or via process_query
    if asi.hive_mind:
        response = asi.hive_mind.process_task({"query": query})
        if response.get("ok"):
            print(f"✅ Hive Mind Responded:")
            print(f"   Stats: {response.get('stats')}")
            print(f"   Text Snippet: {response.get('text')[:200]}...")
            if "WE" in response.get("text", ""):
                print("   ✅ Persona Check: 'WE' detected.")
            else:
                print("   ⚠️ Persona Check: 'WE' NOT detected.")
        else:
            print(f"❌ Hive Mind Failed: {response.get('error')}")
    else:
        print("❌ Hive Mind Engine not loaded.")

def test_counterfactual(asi):
    print_header("TEST 2: COUNTERFACTUAL EXPLORER")
    scenario = "Global energy systems collapse"
    print(f"❓ Scenario: {scenario}")
    
    if asi.counterfactual_explorer:
        response = asi.counterfactual_explorer.process_task({"text": scenario})
        variants = response.get("variants", [])
        if variants:
            print(f"✅ Generated {len(variants)} variants:")
            for v in variants:
                print(f"   - What if {v['scenario']}? -> {v['reason']}")
        else:
            print("❌ No variants generated.")
    else:
        print("❌ Counterfactual Explorer not loaded.")

def test_simulation(asi):
    print_header("TEST 3: ADVANCED SIMULATION ENGINE")
    if hasattr(asi, 'discovered_modules') and 'AdvancedSimulationEngine' in asi.discovered_modules:
        sim_engine = asi.discovered_modules['AdvancedSimulationEngine']
    elif hasattr(asi, 'unified_system') and asi.unified_system:
        # Try to find it in registry
        sim_engine = asi.engine_registry.get('AdvancedSimulationEngine')
        # If not in registry, try to load it dynamically
        if not sim_engine:
             try:
                 from repo_copy.Core_Engines.Advanced_Simulation_Engine import AdvancedSimulationEngine
                 sim_engine = AdvancedSimulationEngine()
             except:
                 pass
    else:
        # Manual load for test
        try:
            from Core_Engines.Advanced_Simulation_Engine import AdvancedSimulationEngine
            sim_engine = AdvancedSimulationEngine()
        except ImportError:
            sim_engine = None

    if sim_engine:
        payload = {
            "scenario": "Market Crash",
            "variables": {"price": 100, "volatility": 0.5},
            "steps": 5
        }
        result = sim_engine.process_task(payload)
        if result.get("ok"):
            print(f"✅ Simulation Successful:")
            print(f"   Final State: {result.get('final_state')}")
            print(f"   Time Series (First 3): {result.get('time_series')[:3]}")
        else:
            print("❌ Simulation Failed.")
    else:
        print("⚠️ AdvancedSimulationEngine not found in standard paths. Attempting discovery...")
        # Trigger discovery
        asi.discover_unused_capabilities()
        if 'AdvancedSimulationEngine' in asi.discovered_modules:
             print("✅ Discovered! Retrying test...")
             test_simulation(asi) # Recurse once
        else:
             print("❌ Could not load AdvancedSimulationEngine.")

def test_full_flow(asi):
    print_header("TEST 4: FULL AWAKENED FLOW")
    query = "Analyze the impact of AI on future economics."
    response = asi.process_query(query)
    print(f"💡 Final Response Length: {len(response)} chars")
    print(f"💡 FULL RESPONSE:\n{'-'*40}\n{response}\n{'-'*40}")

if __name__ == "__main__":
    print("🚀 STARTING REAL INTEGRATION TEST...")
    
    # Initialize
    asi = AGL_Super_Intelligence()
    
    # Run Tests
    test_hive_mind(asi)
    test_counterfactual(asi)
    test_simulation(asi)
    test_full_flow(asi)
    
    print("\n✅ TEST COMPLETE.")
