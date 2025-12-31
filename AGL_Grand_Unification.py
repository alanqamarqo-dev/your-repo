import numpy as np
import time
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

# Import the specialized modules
try:
    from AGL_Quantum_Data_Analysis import QuantumDataAnalyzer
    from AGL_Causal_Learning import CausalLearningAgent
    from AGL_Vectorized_Memory import VectorizedMemoryManager
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    sys.exit(1)

class QuantumCausalUniverse:
    """
    The Grand Unification Engine.
    Combines Quantum Mechanics (Wave Functions) with Causal Logic (Graph Theory).
    """
    def __init__(self):
        print("🌌 Initializing Quantum-Causal Universe...")
        self.quantum_engine = QuantumDataAnalyzer()
        self.causal_engine = CausalLearningAgent()
        self.memory = VectorizedMemoryManager()
        
        # Physical Constants
        self.h_bar = 1.0545718e-34
        self.G = 6.67430e-11
        
        # Universe State (Particles)
        self.particles = []
        
    def create_particle(self, mass, position, velocity):
        """Creates a particle with quantum properties."""
        particle = {
            "id": len(self.particles) + 1,
            "mass": mass,
            "position": np.array(position, dtype=float),
            "velocity": np.array(velocity, dtype=float),
            "wave_function": None # To be calculated
        }
        # Initial Quantum State (Wave Packet)
        # psi = exp(i * (px - Et) / h_bar) -> simplified for simulation
        momentum = mass * np.linalg.norm(velocity)
        particle["wave_function"] = np.exp(1j * momentum / self.h_bar)
        
        self.particles.append(particle)
        print(f"   ✨ Particle {particle['id']} created at {position}")
        
        # Register in Causal Graph
        self.causal_engine.update_belief(f"Create_Particle_{particle['id']}", "Exist")

    def apply_forces_and_logic(self):
        """
        The Core Unification Loop:
        1. Calculate Physical Forces (Gravity).
        2. Calculate Quantum Interference.
        3. Check Causal Consistency (Paradox Check).
        """
        print("\n🔄 Running Simulation Step...")
        
        # 1. Classical/Quantum Hybrid Physics
        for p in self.particles:
            # Apply Gravity (Simplified towards center 0,0,0)
            r = np.linalg.norm(p["position"])
            if r > 1e-9:
                force_mag = (self.G * p["mass"] * 1e24) / (r**2) # Attracted to a massive core
                force_dir = -p["position"] / r
                acceleration = (force_dir * force_mag) / p["mass"]
                
                # Update Kinematics
                p["velocity"] += acceleration
                p["position"] += p["velocity"]
                
                # Update Quantum State (Phase Shift due to Gravity)
                # Gravitational potential V = -GMm/r
                potential = -(self.G * 1e24 * p["mass"]) / r
                phase_shift = np.exp(-1j * potential * 1e-30) # Scaled for simulation
                p["wave_function"] *= phase_shift

        # 2. Quantum Analysis
        positions = np.array([np.linalg.norm(p["position"]) for p in self.particles])
        quantum_state = self.quantum_engine.analyze_dataset(positions)
        print(f"   ⚛️ Quantum State Classification: {quantum_state}")

        # 3. Causal Logic Check
        # If Quantum State is "Destructive", it might imply a paradox or collapse
        action = "Evolve_Universe"
        outcome = "Stable" if "Constructive" in quantum_state else "Collapse"
        
        self.causal_engine.update_belief(action, outcome)
        
        is_safe = self.causal_engine.is_safe_action(action)
        if not is_safe:
            print("   ⚠️ CAUSAL PARADOX DETECTED! Halting simulation to prevent loop.")
            return False
            
        # 4. Memorize State
        state_vector = np.concatenate([p["position"] for p in self.particles])
        # Pad or trim to fit memory if needed, for now just store raw
        try:
            self.memory.add_memory(state_vector)
            print("   💾 Universe State Memorized.")
        except Exception as e:
            print(f"   ⚠️ Memory Error: {e}")

        return True

    def run_simulation(self, steps=5):
        for i in range(steps):
            print(f"\n--- Time Step {i+1} ---")
            if not self.apply_forces_and_logic():
                break
            time.sleep(0.5)

if __name__ == "__main__":
    universe = QuantumCausalUniverse()
    
    # Create a small solar system
    universe.create_particle(mass=10.0, position=[100, 0, 0], velocity=[0, 2, 0])
    universe.create_particle(mass=5.0, position=[150, 0, 0], velocity=[0, 1.5, 0])
    
    universe.run_simulation(steps=5)
    
    print("\n✅ Grand Unification Simulation Complete.")
