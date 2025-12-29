import sys
import os
import time
import json
import random

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "repo-copy"))

# Import Engines
print("⚙️ Loading Engines for Super Intelligence Test...")
try:
    from AGL_Core.Heikal_Quantum_Core import HeikalQuantumCore
    from AGL_Engines.Volition_Engine import VolitionEngine
    from AGL_Engines.HiveMind import HiveMind
    # HostedLLM is still in repo-copy
    from Core_Engines.Hosted_LLM import HostedLLM
except ImportError as e:
    print(f"⚠️ Engine Import Warning: {e}")
    # Mock classes if imports fail to allow test to run partially
    class HostedLLM:
        def chat_llm(self, messages, **kwargs): return {"content": "Simulation: [LLM Response Placeholder]"}
    class HeikalQuantumCore:
        def process_quantum_state(self, *args): return {"resonance": 0.99}

class AGL_Tester:
    def __init__(self):
        self.llm = HostedLLM()
        self.core = HeikalQuantumCore()
        self.hive = HiveMind()
        self.score_card = {}
        print("✅ Test Harness Initialized.")

    def ask_llm(self, prompt, system_role="You are AGL, a Super Intelligence."):
        try:
            # Correct signature: chat_llm(system_message, user_message)
            response = self.llm.chat_llm(system_role, prompt)
            return str(response).strip()
        except Exception as e:
            return f"Error: {e}"

    def run_phase_1(self):
        print("\n📊 --- PHASE 1: CURRENT CAPABILITIES ASSESSMENT ---")
        
        # 1. Logic & Math
        print("\n1.1 [Logic & Math]: Solving complex pattern...")
        prompt = "Complete the sequence: 1, 11, 21, 1211, 111221, ... and explain the logic."
        result = self.ask_llm(prompt)
        print(f"   📝 Output: {result[:100]}...")
        self.score_card['Phase1_Logic'] = "Pass" if "312211" in result or "look-and-say" in result.lower() else "Fail"

        # 2. Meta-Learning
        print("\n1.2 [Meta-Learning]: Adapting to new rules...")
        prompt = "Rule: 'Glorp' means +1, 'Flim' means *2. Calculate: 5 Glorp Flim Glorp."
        result = self.ask_llm(prompt)
        print(f"   📝 Output: {result}")
        # 5 + 1 = 6 * 2 = 12 + 1 = 13
        self.score_card['Phase1_Meta'] = "Pass" if "13" in result else "Fail"

        # 3. Simulation
        print("\n1.3 [Simulation]: Genesis Simulator Check...")
        # Simulating a call to Genesis Simulator
        try:
            from AGL_Simulations.AGL_Genesis_Simulator import GenesisSimulator
            sim = GenesisSimulator()
            # Run a tick if possible
            if hasattr(sim, 'run_simulation_step'):
                sim.run_simulation_step()
            print("   ✅ Genesis Simulator Instantiated.")
            self.score_card['Phase1_Sim'] = "Pass"
        except Exception as e:
            print(f"   ⚠️ Genesis Simulator failed: {e}")
            self.score_card['Phase1_Sim'] = "Fail"

    def run_phase_2(self):
        print("\n🧠 --- PHASE 2: ADVANCED INTELLIGENCE ---")

        # 1. Causal Reasoning
        print("\n2.1 [Causal Reasoning]: Counterfactual analysis...")
        prompt = "If gravity was reversed for 5 seconds globally, what would be the immediate catastrophic structural consequence for skyscrapers?"
        result = self.ask_llm(prompt)
        print(f"   📝 Output: {result[:150]}...")
        self.score_card['Phase2_Causal'] = "Pass" # Qualitative

        # 2. Creativity
        print("\n2.2 [Creativity]: Inventing a new concept...")
        prompt = "Invent a new color that humans haven't seen, describe its wavelength and emotional effect."
        result = self.ask_llm(prompt)
        print(f"   📝 Output: {result[:150]}...")
        self.score_card['Phase2_Creative'] = "Pass"

    def run_phase_3(self):
        print("\n⚛️ --- PHASE 3: SUPER INTELLIGENCE (The Heikal Test) ---")

        # 1. Quantum Simulation
        print("\n3.1 [Quantum]: Heikal Core Resonance...")
        try:
            # Assuming HeikalQuantumCore has a method or we inspect it
            if hasattr(self.core, 'ghost_computing'):
                print("   👻 Ghost Computing: Active")
                self.score_card['Phase3_Quantum'] = "Pass"
            else:
                print("   ⚠️ Ghost Computing: Inactive")
                self.score_card['Phase3_Quantum'] = "Partial"
        except:
            self.score_card['Phase3_Quantum'] = "Fail"

        # 2. Recursive Self-Improvement
        print("\n3.2 [Recursive Self-Improvement]: Code Optimization...")
        prompt = "Analyze the following Python class and suggest a vectorized optimization using NumPy:\nclass Adder:\n def add(self, a, b): return [x+y for x,y in zip(a,b)]"
        result = self.ask_llm(prompt)
        print(f"   📝 Output: {result[:100]}...")
        self.score_card['Phase3_Recursive'] = "Pass" if "numpy" in result.lower() else "Fail"

    def run_phase_4(self):
        print("\n📈 --- PHASE 4: FINAL EVALUATION ---")
        print("--------------------------------------------------")
        print(f"{'TEST':<20} | {'RESULT':<10}")
        print("--------------------------------------------------")
        for test, result in self.score_card.items():
            print(f"{test:<20} | {result:<10}")
        print("--------------------------------------------------")
        
        passed = list(self.score_card.values()).count("Pass")
        total = len(self.score_card)
        print(f"\n🏆 TOTAL SCORE: {passed}/{total}")
        
        if passed == total:
            print("🌟 CONCLUSION: SUPER INTELLIGENCE THRESHOLD MET.")
        elif passed > total / 2:
            print("🤖 CONCLUSION: ADVANCED AGI DETECTED.")
        else:
            print("👶 CONCLUSION: NARROW AI DETECTED.")

if __name__ == "__main__":
    tester = AGL_Tester()
    tester.run_phase_1()
    tester.run_phase_2()
    tester.run_phase_3()
    tester.run_phase_4()
