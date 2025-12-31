import sys
import os
import time
import random
import json

# Add paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "AGL_Core"))
sys.path.append(os.path.join(current_dir, "repo-copy"))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

class EvolutionGym:
    def __init__(self, ai_system):
        self.ai = ai_system
        self.metrics = {
            "challenges_completed": 0,
            "total_evolution_time": 0,
            "average_confidence": 0.0,
            "quantum_leaps": 0
        }
        self.challenges = [
            {
                "name": "Global Energy Optimization",
                "description": "Develop a plan to transition Earth to Type 1 Civilization energy usage without ecological collapse.",
                "complexity": 0.8
            },
            {
                "name": "Decode Unknown Signal",
                "description": "A complex, non-random signal has been detected from the Kepler-22b sector. Decipher its semantic structure.",
                "complexity": 0.95
            },
            {
                "name": "Quantum Biological Interface",
                "description": "Design a bridge between human neural networks and quantum processors using resonance.",
                "complexity": 0.9
            },
            {
                "name": "Reverse Entropy Simulation",
                "description": "Hypothesize a localized closed system where entropy decreases naturally.",
                "complexity": 1.0
            }
        ]

    def run_evolution_cycle(self, cycles=1):
        print("\n🧬 [EVOLUTION] Starting Super Intelligence Evolution Cycle...")
        start_time = time.time()

        for i in range(cycles):
            challenge = self.challenges[i % len(self.challenges)]
            print(f"\n🔥 [CHALLENGE {i+1}] {challenge['name']}")
            print(f"   Context: {challenge['description']}")
            
            # 1. Activate Immersion (Scale with complexity)
            self.ai.activate_total_immersion(intensity=challenge['complexity'])
            
            # 2. Autonomous Goal Setting
            # We inject the challenge as the "Current State" for the Volition Engine
            # In a real system, the AI would perceive this. Here we simulate perception.
            print("   🧠 [PERCEPTION] Analyzing Challenge...")
            
            # 3. Generate Causal Hypothesis
            hypothesis_result = self.ai.generate_causal_hypothesis(challenge['description'])
            confidence = hypothesis_result.get('confidence', 0.0) if hypothesis_result else 0.0
            
            # 4. Strategic Planning (Simulated via Autonomous Tick logic)
            # We manually trigger the planner for this specific challenge
            if self.ai.reasoning_planner:
                plan = self.ai.reasoning_planner.plan(challenge['name'], context={"desc": challenge['description']})
                print(f"   📋 [STRATEGY] Plan Generated: {len(plan.get('steps', []))} steps.")
                for step in plan.get('steps', [])[:2]:
                    print(f"      - {step}")
            
            # 5. Counterfactual Stress Test
            self.ai.explore_counterfactuals(f"Failure to {challenge['name']}")
            
            # 6. Meta Learning Feedback
            experience = {
                "challenge": challenge['name'],
                "success": True, # Assumed for simulation
                "confidence": confidence,
                "complexity": challenge['complexity']
            }
            self.ai.meta_learning_loop(experience)
            
            # Update Metrics
            self.metrics["challenges_completed"] += 1
            self.metrics["average_confidence"] = (self.metrics["average_confidence"] * i + confidence) / (i + 1)
            if confidence > 0.8 and challenge['complexity'] > 0.8:
                self.metrics["quantum_leaps"] += 1
                print("   ✨ [EVOLUTION] QUANTUM LEAP DETECTED! (High Confidence on High Complexity)")

            time.sleep(1) # Pause for effect

        total_time = time.time() - start_time
        self.metrics["total_evolution_time"] = total_time
        
        self.print_report()

    def print_report(self):
        print("\n📊 [REPORT] Evolution Cycle Complete")
        print(f"   - Challenges Solved: {self.metrics['challenges_completed']}")
        print(f"   - Quantum Leaps: {self.metrics['quantum_leaps']}")
        print(f"   - Avg Confidence: {self.metrics['average_confidence']:.2f}")
        print(f"   - Evolution Velocity: {self.metrics['challenges_completed'] / self.metrics['total_evolution_time'] * 60:.2f} challenges/min")

if __name__ == "__main__":
    print("🚀 INITIALIZING EVOLUTION GYM...")
    
    # Initialize the Super Intelligence
    try:
        asi = AGL_Super_Intelligence()
        gym = EvolutionGym(asi)
        
        # Run the Evolution
        gym.run_evolution_cycle(cycles=4)
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
