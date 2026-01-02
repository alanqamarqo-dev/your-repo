import sys
import os
import numpy as np
import time

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Resonance_Optimizer import ResonanceOptimizer

def objective_function(x):
    """
    A landscape with local maxima and one global maximum.
    f(x) = x * sin(x) + x/2
    """
    return x * np.sin(x) + x/0.5

def run_demo():
    print("🌌 Initializing Quantum-Synaptic Resonance Demo...")
    optimizer = ResonanceOptimizer(barrier_width=0.5)
    
    # --- Demo 1: Quantum Tunneling Search ---
    print("\n🧪 Experiment 1: Quantum Tunneling vs. Classical Search")
    print("   Goal: Find global maximum in a rugged landscape.")
    
    # Setup landscape
    x_space = np.linspace(0, 20, 100)
    landscape = objective_function(x_space)
    global_max_idx = np.argmax(landscape)
    global_max_val = landscape[global_max_idx]
    
    print(f"   Global Max Value: {global_max_val:.4f} at index {global_max_idx}")
    
    # Start both agents at a local maximum (trap)
    start_idx = 10 # A poor local max
    current_idx_classical = start_idx
    current_idx_quantum = start_idx
    
    print(f"   Starting at index: {start_idx} (Value: {landscape[start_idx]:.4f})")
    
    steps = 50
    print(f"   Running {steps} steps...")
    
    for i in range(steps):
        # Propose a random move (neighbor)
        move = np.random.choice([-1, 1])
        
        # --- Classical Agent (Greedy) ---
        next_idx_c = np.clip(current_idx_classical + move, 0, 99)
        if landscape[next_idx_c] > landscape[current_idx_classical]:
            current_idx_classical = next_idx_c
            
        # --- Quantum Agent (Resonance) ---
        next_idx_q = np.clip(current_idx_quantum + move, 0, 99)
        current_score = landscape[current_idx_quantum]
        next_score = landscape[next_idx_q]
        
        # Use the optimizer to decide
        accept, prob = optimizer.optimize_search(current_score, next_score, temperature=2.0)
        if accept:
            current_idx_quantum = next_idx_q
            
    print(f"\n   🏁 Results:")
    print(f"   Classical Agent Final Value: {landscape[current_idx_classical]:.4f} (Index: {current_idx_classical})")
    print(f"   Quantum Agent Final Value:   {landscape[current_idx_quantum]:.4f} (Index: {current_idx_quantum})")
    
    if landscape[current_idx_quantum] > landscape[current_idx_classical]:
        print("   ✅ Quantum Tunneling escaped the local minimum!")
    else:
        print("   ⚠️ Both agents stuck or equal.")

    # --- Demo 2: Resonance Amplification ---
    print("\n🧪 Experiment 2: Resonance Amplification Filter")
    print("   Goal: Identify the 'Genius Idea' from noise.")
    
    target_freq = 5.0 # The "Truth"
    
    # Generate random ideas with 'frequencies' (metrics)
    ideas = []
    for i in range(10):
        freq = np.random.uniform(0, 10)
        ideas.append({'id': f'Idea_{i}', 'metric': freq, 'content': 'Random Noise'})
        
    # Inject the "Genius Idea" (close to target)
    ideas.append({'id': 'Genius_Idea', 'metric': 5.01, 'content': 'E=mc^2'})
    
    print(f"   Target Frequency: {target_freq}")
    print("   Filtering 11 ideas...")
    
    filtered = optimizer.filter_solutions(ideas, target_freq)
    
    print("\n   🏆 Top 3 Amplified Ideas:")
    for i, idea in enumerate(filtered[:3]):
        print(f"   {i+1}. {idea['id']} | Raw Metric: {idea['metric']:.2f} | Resonance Score: {idea['resonance_score']:.2f} (Amp: {idea['amplification']:.1f}x)")
        
    if filtered[0]['id'] == 'Genius_Idea':
        print("   ✅ Resonance Filter successfully isolated the Genius Idea!")

if __name__ == "__main__":
    run_demo()
