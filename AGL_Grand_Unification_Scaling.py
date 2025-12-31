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

class ScaledQuantumUniverse:
    def __init__(self, num_particles=1000000):
        print(f"🌌 Initializing MASSIVE SCALED Quantum-Causal Universe ({num_particles} Agents)...")
        self.quantum_engine = QuantumDataAnalyzer()
        self.causal_engine = CausalLearningAgent()
        self.memory = VectorizedMemoryManager()
        self.num_particles = num_particles
        
        # Dynamic Physics Parameters
        self.physics_params = {
            "G": 6.67430e-11,
            "core_mass": 1e24,
            "damping": 1.0 # Initially no damping
        }
        
        # Initialize Particles using Vectorized Arrays (Structure of Arrays)
        # This is much faster for 1M+ particles than a list of dicts
        print("   ✨ Generating Agent Population (Vectorized)...")
        
        # Position: (N, 3)
        self.positions = np.random.randn(num_particles, 3).astype(np.float32) * 100 
        
        # Velocity: (N, 3)
        self.velocities = np.random.randn(num_particles, 3).astype(np.float32) * 0.5
        
        # Mass: (N, 1)
        self.masses = (np.random.rand(num_particles, 1).astype(np.float32) * 1000 + 1)
        
        # Wave Function: (N,) Complex
        self.wave_functions = np.exp(1j * np.random.rand(num_particles).astype(np.float32) * 2 * np.pi)
        
        print(f"   ✅ Population Ready. Memory Usage: ~{self.positions.nbytes * 4 / 1024 / 1024:.2f} MB for state.")

    def run_simulation_step(self):
        """
        Runs one simulation step using Vectorized Numpy Operations.
        """
        start_time = time.time()
        
        G = self.physics_params["G"]
        core_mass = self.physics_params["core_mass"]
        damping = self.physics_params["damping"]
        
        # 1. Vectorized Physics Update
        # Calculate distances to center (0,0,0)
        # r shape: (N, 1)
        r = np.linalg.norm(self.positions, axis=1, keepdims=True)
        
        # Avoid division by zero
        r[r < 1e-9] = 1e-9
        
        # Force Magnitude: F = G * m * M / r^2
        # shape: (N, 1)
        force_mag = (G * self.masses * core_mass) / (r**2)
        
        # Force Direction: -pos / r
        # shape: (N, 3)
        force_dir = -self.positions / r
        
        # Acceleration: F / m
        # shape: (N, 3)
        acceleration = (force_dir * force_mag) / self.masses
        
        # Update Kinematics
        self.velocities += acceleration
        self.velocities *= damping # Apply Damping
        self.positions += self.velocities
        
        # Update Quantum State (Phase Shift)
        # Potential V = -GmM/r
        potential = -(G * core_mass * self.masses) / r
        # Phase shift = exp(-i * V * t / h_bar) -> simplified constant
        phase_shift = np.exp(-1j * potential.flatten() * 1e-30)
        self.wave_functions *= phase_shift
        
        # 2. Quantum Analysis (Global State)
        # Analyze the "Price" (Position magnitude) distribution
        # We take a subset for analysis if N is too large to avoid slow SVD/Analysis
        analysis_subset_size = min(10000, self.num_particles)
        raw_data = r[:analysis_subset_size].flatten()
        
        # Normalize data to avoid overflow when dividing by h_bar (1e-34)
        # We map the macroscopic values to a quantum scale for analysis
        max_val = np.max(raw_data)
        if max_val > 0:
            # Scale data so that the max value corresponds to a phase of 2*pi when divided by h_bar
            # target = data / h_bar  => data = target * h_bar
            target_scale = 1.0545718e-34 * 2 * np.pi 
            normalized_data = (raw_data / max_val) * target_scale
        else:
            normalized_data = raw_data

        quantum_state = self.quantum_engine.analyze_dataset(normalized_data)
        
        # 3. Causal Logic Check
        # Calculate average momentum magnitude
        momenta = np.linalg.norm(self.velocities, axis=1)
        avg_momentum = np.mean(momenta)
        
        action = "Market_Evolution"
        
        # Thresholds
        if avg_momentum < 50:
            outcome = "Stable"
        elif avg_momentum < 100:
            outcome = "Volatile"
        else:
            outcome = "Critical_Collapse"
            
        self.causal_engine.update_belief(action, outcome)
        
        end_time = time.time()
        duration = end_time - start_time
        
        dps = self.num_particles / duration
        print(f"   ⏱️ Step Complete in {duration:.4f}s | Momentum: {avg_momentum:.2f} | Speed: {dps/1e6:.2f}M decisions/sec | Outcome: {outcome}")
        return outcome

    def run_evolution(self, steps=10):
        print(f"\n🚀 Starting Evolution Cycle ({steps} steps) for {self.num_particles} Agents...")
        for i in range(steps):
            print(f"   --- Step {i+1} ---")
            outcome = self.run_simulation_step()
            
            if outcome == "Volatile" or outcome == "Critical_Collapse":
                print(f"   ⚠️ {outcome} Detected - ACTIVATING DEFENSES...")
                
                # Real Adjustment: Increase Damping (Cooling the market)
                current_damping = self.physics_params["damping"]
                new_damping = max(0.5, current_damping * 0.9) # Reduce velocity by 10% per step
                self.physics_params["damping"] = new_damping
                
                print(f"      🔧 Damping Factor Adjusted: {current_damping:.4f} -> {new_damping:.4f}")
            
            elif outcome == "Stable" and self.physics_params["damping"] < 1.0:
                 # Relax controls if stable
                 self.physics_params["damping"] = min(1.0, self.physics_params["damping"] * 1.05)
                 print(f"      🟢 System Stable - Relaxing Damping: {self.physics_params['damping']:.4f}")

        print("\n✅ Evolution Cycle Complete.")
        
        # Store Final State in Vectorized Memory
        print("💾 Archiving Final State to Vectorized Memory...")
        # Store a representative sample
        final_state_vector = np.linalg.norm(self.positions[:512], axis=1)
        
        summary_vector = np.zeros(512)
        summary_vector[:min(len(final_state_vector), 512)] = final_state_vector[:min(len(final_state_vector), 512)]
        
        self.memory.add_memory(summary_vector)
        print("   ✅ State Archived.")

if __name__ == "__main__":
    # Scale: 1,000,000 particles
    sim = ScaledQuantumUniverse(num_particles=1000000)
    
    # Inject High Energy to trigger the protection system
    print("⚡ INJECTING HIGH ENERGY TO TRIGGER VOLATILITY...")
    sim.velocities *= 100.0 
        
    sim.run_evolution(steps=10)
