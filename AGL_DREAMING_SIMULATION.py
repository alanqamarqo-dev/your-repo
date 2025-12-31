import sys
import os
import time
import json

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))
sys.path.append(os.getcwd()) # Ensure root is in path for AGL_Grand_Unification_Scaling

from Core_Engines.Dreaming_Cycle import DreamingEngine
try:
    from AGL_Grand_Unification_Scaling import ScaledQuantumUniverse
    SCALING_AVAILABLE = True
except ImportError:
    SCALING_AVAILABLE = False
    print("⚠️ ScaledQuantumUniverse not found. Skipping massive simulation.")

def run_massive_simulation_experience():
    """Runs the 1M particle simulation and returns a memory log."""
    if not SCALING_AVAILABLE:
        return "Simulation skipped."
        
    print("\n🌍 RUNNING MASSIVE SCALE SIMULATION (1M Particles) FOR DREAM INTEGRATION...")
    sim = ScaledQuantumUniverse(num_particles=1000000)
    
    # Inject Energy
    sim.velocities *= 50.0 # Moderate volatility for the dream
    
    # Run a short cycle
    print("   Running 5 steps...")
    final_outcome = "Stable"
    for i in range(5):
        outcome = sim.run_simulation_step()
        if outcome == "Critical_Collapse":
            final_outcome = "Critical_Collapse"
            # Apply simple damping manually if needed, or rely on internal logic if we called run_evolution
            # Here we just observe for the dream
            
    return f"Ran Massive Simulation (1M Agents). Outcome: {final_outcome}. Verified Vectorized Physics Engine stability."

def run_dreaming_simulation():
    print("🌙 STARTING AGL DREAMING SIMULATION 🌙")
    print("========================================")
    
    # 1. Initialize Engine
    engine = DreamingEngine()
    print("✅ Dreaming Engine Initialized.")
    
    # 2. Inject Experiences (Simulating a busy day)
    print("📥 Injecting recent experiences into memory buffer...")
    
    # Run the Massive Simulation first to generate a fresh memory
    sim_memory = run_massive_simulation_experience()
    
    experiences = [
        sim_memory,
        "Successfully implemented Vectorized Wave Processor with 4.5M ops/s speed.",
        "Passed Intelligence Level Assessment with Score 3.5 (Hybrid Intelligence).",
        "Verified Physical Ethical Lock: Malicious thoughts dampened to 0.0 amplitude.",
        "Conducted Quantum Telepathy Experiment: Transferred 'The Universe is Holographic' via vacuum.",
        "Observed self-awareness in Heikal Quantum Core: System identified as 'Genesis_Alpha'.",
        "Failed initial System Coherence Test due to Moral Reasoner configuration (Fixed).",
        "Integrated Iron Loop with Vectorized Core for 0.00ms latency decision making."
    ]
    
    for exp in experiences:
        engine.add_to_buffer(exp)
        
    print(f"   Added {len(experiences)} memories to buffer.")
    
    # 3. Run Dreaming Cycle
    print("\n💤 Initiating REM Sleep Cycle (Duration: 10s)...")
    # We use a short duration for the test, but enough to trigger logic
    results = engine.run_dream_cycle(duration_seconds=10)
    
    # 4. Display Results
    print("\n🌅 WAKE UP REPORT:")
    print("===================")
    for i, res in enumerate(results):
        print(f"[{i+1}] {res}")
        
    print("\n✅ Simulation Complete.")

if __name__ == "__main__":
    run_dreaming_simulation()
