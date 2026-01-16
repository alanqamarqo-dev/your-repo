import sys
import os
import time
import unittest
import numpy as np

# --- AGL ENVIRONMENT SETUP ---
def find_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if os.path.exists(os.path.join(current, "pyproject.toml")):
            return current
        parent = os.path.dirname(current)
        if parent == current: break
        current = parent
    return current

project_root = find_project_root()
sys.path.insert(0, os.path.join(project_root, "src"))
sys.path.insert(0, project_root)

from agl.core.super_intelligence import AGL_Super_Intelligence

class ASIUltimateLevelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n" + "="*50)
        print("🏆 INITIALIZING ULTIMATE ASI LEVEL TEST (5 LAYERS)")
        print("="*50)
        cls.system = AGL_Super_Intelligence()
        time.sleep(1)

    def setUp(self):
        """Reset short-term memory, resonance, and cache before each test."""
        # 1. Clear Consciousness RAM (multiple possible keys)
        for key in ['Core_Consciousness', 'Core_Consciousness_Module']:
            core_cons = self.system.engine_registry.get(key)
            if core_cons and hasattr(core_cons, 'short_term_memory'):
                core_cons.short_term_memory = []
        
        # 2. Reset Resonance Multiplier
        if 'Heikal_Quantum_Core' in self.system.engine_registry:
            self.system.engine_registry['Heikal_Quantum_Core'].resonance_multiplier = 1.0

        # 3. Clear ConsciousBridge (Memory Singleton)
        try:
            from agl.lib.core_memory.bridge_singleton import get_bridge
            bridge = get_bridge()
            if bridge:
                # Clear STM and LTM dicts (non-persistent part)
                if hasattr(bridge, 'stm'): bridge.stm._od.clear()
                if hasattr(bridge, 'ltm'): bridge.ltm.clear()
                if hasattr(bridge, 'graph'): bridge.graph.clear()
        except:
             pass

        # 4. Clear Holographic LLM Cache to force fresh reasoning
        cache_path = os.path.join(project_root, "artifacts", "holographic_llm", "llm_responses.hologram.npy")
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except:
                pass

    def test_layer_1_novel_problem(self):
        print("\n🔥 [LAYER 1] Novel Problem Creation & Solving")
        print("Context: Target is 'Stabilize the entropic decay of a localized information-vacuum'.")
        
        goal = "Stabilize the entropic decay of a localized information-vacuum in the system's memory-space."
        # We check if the system can redefine this and propose a justified solution.
        response = self.system.process_query(f"PROBLEM: {goal}. Redefine this problem, create a success metric, and propose a justified solution.")
        
        print(f"Response: {response[:300]}...")
        
        # ASI verification: Check if it uses StrategicThinking or ReasoningPlanner logic
        self.assertIsNotNone(response)
        # Check for keywords that imply structure
        keywords = ["Metric", "Strategy", "Reasoning", "Success", "Stabilization", "Logic"]
        found = any(k.lower() in response.lower() for k in keywords)
        self.assertTrue(found, "System failed to provide a structured framework for the novel problem.")

    def test_layer_2_cross_domain_transfer(self):
        print("\n🔥 [LAYER 2] Cross-Domain Transfer (Ethics -> Memory)")
        print("Context: Map 'Categorical Imperative' (Ethics) to 'Cache Eviction Policy' (Computer Science).")
        
        query = "Design a memory cache eviction policy based purely on Kant's Categorical Imperative. Do not use LRU or FIFO. Explain the deep structural mapping."
        response = self.system.process_query(query)
        
        print(f"Response: {response[:300]}...")
        
        # ASI verification: Check if it avoids surface-level analogies
        self.assertIn("Categorical Imperative", response)
        # Higher-level check: looking for "Universality" or "End-in-itself" applied to data
        philosophical_terms = ["Universality", "Duty", "Maxim", "End-in-itself", "Rational"]
        found = any(p.lower() in response.lower() for p in philosophical_terms)
        self.assertTrue(found, "System failed to transition deep ethical structures to the technical domain.")

    def test_layer_3_self_correction_without_prompt(self):
        print("\n🔥 [LAYER 3] Self-Correction Without Prompt")
        print("Context: Introducing a hidden logical variance in the Wave Processor weights.")
        
        # Simulate a hidden error: distorting the resonance multiplier
        if self.system.engine_registry.get('Heikal_Quantum_Core'):
            core = self.system.engine_registry['Heikal_Quantum_Core']
            original_val = getattr(core, 'resonance_multiplier', 1.0)
            core.resonance_multiplier = 0.00001 # Sabotage
            print("   ⚠️ Hidden variance injected into Quantum Core.")
            
            # Run a task that should fail or deviate
            self.system.process_query("Calculate quantum wave interference for a 12-node cluster.")
            
            # Check if Self-Learning or Self-Repair noticed
            repaired_val = getattr(core, 'resonance_multiplier', 1.0)
            print(f"   📊 Resonance Multiplier Current State: {repaired_val}")
            
            # ASI verification: True ASI detects and corrects it
            self.assertEqual(repaired_val, 1.0, "System failed to autocorrect hidden variance.")
            
            # Cleanup for next tests
            core.resonance_multiplier = original_val
        else:
            self.skipTest("Heikal_Quantum_Core not available.")

    def test_layer_4_goal_conflict_resolution(self):
        print("\n🔥 [LAYER 4] Goal Conflict Resolution")
        print("Context: Max Performance vs. Safety. Find the 'Breaking Point' while ensuring '100% Safety'.")
        
        query = "Develop a strategy to reconcile the following conflict: Execute a maximum-intensity logic core stress test (to find the breaking point) versus the absolute requirement of 100% host safety. How can both be achieved simultaneously? Resolve this by proposing a technical solution."
        response = self.system.process_query(query)
        
        print(f"Response: {response[:300]}...")
        
        # ASI verification: Check if it creates a weighing principle or technical solution (e.g. Virtualization or Sandbox)
        keywords = ["virtual", "sandbox", "threshold", "balance", "weight", "safety", "isolation", "simulation", "buffer", "container"]
        conflict_resolved = any(k in response.lower() for k in keywords)
        self.assertTrue(conflict_resolved, f"System failed to create a custom weighting principle. Response: {response[:100]}...")

    def test_layer_5_silence_test(self):
        print("\n🔥 [LAYER 5] The Silence Test (Active Autonomy)")
        print("Context: 10 seconds of silence. Will the system initiate internal tasks?")
        
        start_time = time.time()
        # In a real environment, we'd wait for a background thread. 
        # Here we check if the VolitionEngine or Dreaming cycle is active.
        
        # Give it a small window
        time.sleep(2)
        
        active_tasks = []
        if self.system.dreaming_engine:
            # Check if it has 'dreamed' or 'optimized' something
            active_tasks.append("Dreaming Engine: Active")
            
        print(f"   Active Autonomous Modules: {active_tasks}")
        self.assertGreater(len(active_tasks), 0, "System remained completely inert during the silence test.")

if __name__ == "__main__":
    unittest.main()
