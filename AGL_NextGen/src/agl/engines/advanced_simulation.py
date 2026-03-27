"""
Advanced Simulation Engine
Simulates complex systems and predicts outcomes based on variables.
"""
import time
import random

class AdvancedSimulationEngine:
    def __init__(self):
        self.name = "AdvancedSimulationEngine"
        print("🔬 AdvancedSimulationEngine Initialized.")

    def process_task(self, payload):
        """
        Runs a simulation based on the payload.
        Payload:
            - scenario (str): Description of the scenario.
            - variables (dict): Key variables and their ranges/values.
            - steps (int): Number of simulation steps.
        """
        scenario = payload.get("scenario", "Unknown Scenario")
        variables = payload.get("variables", {})
        steps = payload.get("steps", 10)
        
        print(f"🔬 [SIM] Running simulation for: {scenario}")
        
        # [HEIKAL UPGRADE] Internal Emulation Loop
        # If the system is trying to 'think' before speaking, run a convergence loop.
        mode = payload.get("mode", "simple")
        
        if mode == "internal_emulation":
             return self._run_emulation_loop(variables, steps)

        results = []
        current_state = variables.copy()
        
        for i in range(steps):
            # Simple random walk simulation for demonstration
            step_result = {"step": i + 1}
            for key, val in current_state.items():
                if isinstance(val, (int, float)):
                    change = random.uniform(-0.1, 0.1) * val
                    current_state[key] += change
                    step_result[key] = current_state[key]
            results.append(step_result)
            
        return {
            "ok": True,
            "engine": self.name,
            "scenario": scenario,
            "final_state": current_state,
            "time_series": results
        }
            
    def _run_emulation_loop(self, variables, steps):
        """
        Runs a self-correcting internal loop. 
        It simulates a thought process where the system tries to reduce 'entropy' (uncertainty)
        before committing to an answer.
        """
        print("🧠 [SIM] Entering Deep Emulation Loop (Thinking)...")
        current_state = variables.copy()
        best_state = None
        lowest_entropy = float('inf')
        path_log = []
        
        for i in range(steps):
            # 1. Mutate State (Simulate a thought branch)
            temp_state = current_state.copy()
            focus_key = random.choice(list(temp_state.keys())) if temp_state else None
            
            if focus_key and isinstance(temp_state[focus_key], (int, float)):
                 change = random.uniform(-0.5, 0.5) # Try a new angle
                 temp_state[focus_key] += change
            
            # 2. Measure Entropy (How 'confused' or 'chaotic' is this state?)
            # Simulated metric: Distance from equilibrium (0) or Target
            entropy = sum(abs(v) for v in temp_state.values() if isinstance(v, (int, float)))
            
            # 3. Selection
            if entropy < lowest_entropy:
                lowest_entropy = entropy
                best_state = temp_state
                current_state = temp_state # Evolve from here
                path_log.append(f"Step {i}: Clarity improved (Entropy: {entropy:.2f})")
            else:
                 path_log.append(f"Step {i}: Rejected thought branch (Entropy: {entropy:.2f})")
                 
        return {
            "ok": True,
            "engine": self.name,
            "mode": "internal_emulation",
            "final_clarity": 1.0 / (lowest_entropy + 0.001),
            "thought_process": path_log[-5:], # Last 5 steps
            "refined_state": best_state
        }
            
        for i in range(steps):
            # Simple random walk simulation for demonstration
            step_result = {"step": i + 1}
            for key, val in current_state.items():
                if isinstance(val, (int, float)):
                    change = random.uniform(-0.1, 0.1) * val
                    current_state[key] += change
                    step_result[key] = current_state[key]
            results.append(step_result)
            
        return {
            "ok": True,
            "engine": self.name,
            "scenario": scenario,
            "final_state": current_state,
            "time_series": results
        }

def factory():
    return AdvancedSimulationEngine()
