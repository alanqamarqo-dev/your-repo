import sys
import os
import time
import json

# Add repo-copy to path to ensure we can import modules
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from dynamic_modules.mission_control_enhanced import EnhancedMissionController as MissionControl

def run_mission():
    print("=== Starting Resonance Optimizer Experimental Mission ===")
    print("Objective: Optimize Neural Architecture using Quantum Tunneling")
    
    # Initialize Mission Control
    mc = MissionControl()
    
    # Define a complex problem scenario
    # We have several architectural candidates for the next version of AGL.
    # 'energy': Represents the implementation difficulty/cost (Barrier).
    # 'coherence': Represents the theoretical alignment with AGI goals (Resonance).
    # We want high coherence, but high energy usually blocks standard optimizers.
    
    candidates = [
        {
            'id': 'Arch_A_Standard', 
            'description': 'Standard Transformer', 
            'energy': 0.2,  # Low barrier (easy)
            'coherence': 0.4 # Low resonance
        },
        {
            'id': 'Arch_B_Hybrid', 
            'description': 'Hybrid Mamba-Transformer', 
            'energy': 0.6,  # Medium barrier
            'coherence': 0.7 # Medium resonance
        },
        {
            'id': 'Arch_C_Quantum', 
            'description': 'Quantum-Synaptic Resonance Network (The Target)', 
            'energy': 0.95, # Very high barrier (very hard to implement)
            'coherence': 0.99 # Extremely high resonance
        },
        {
            'id': 'Arch_D_Random', 
            'description': 'Random Noise Network', 
            'energy': 0.1, 
            'coherence': 0.01
        }
    ]
    
    print(f"\n[Input] Analyzing {len(candidates)} architectural candidates...")
    for c in candidates:
        print(f"  - {c['id']}: Barrier={c['energy']}, Resonance={c['coherence']}")

    # Construct the task payload
    task_payload = {
        'candidates': candidates,
        'parameters': {
            'tunneling_factor': 0.15, # Allow tunneling
            'amplification_factor': 2.5 # Strong amplification of good ideas
        }
    }

    print("\n[Action] Engaging ResonanceOptimizer engine...")
    start_time = time.time()
    
    # Execute via Mission Control
    # We explicitly request the ResonanceOptimizer engine via simulate_engine (async)
    import asyncio
    
    # simulate_engine signature: (engine_name, task_data, role)
    # It returns a dict with 'raw' containing the engine's return value
    
    async def run_engine():
        # simulate_engine is part of the integration_engine
        return await mc.integration_engine.simulate_engine(
            engine_name="ResonanceOptimizer", 
            task_data=task_payload,
            role="optimizer"
        )
        
    result_wrapper = asyncio.run(run_engine())
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n[Result] Optimization complete in {duration:.4f}s")
    
    if result_wrapper and result_wrapper.get('real_processing'):
        result = result_wrapper.get('raw')
        if result and result.get('status') == 'success':
            best = result['best_candidate']
            print(f"\n>>> WINNER: {best['id']} <<<")
            print(f"    Description: {best['description']}")
            print(f"    Original Resonance: {best['coherence']}")
            print(f"    Amplified Score: {best.get('resonance_score', 'N/A')}")
            
            if best['id'] == 'Arch_C_Quantum':
                print("\n[SUCCESS] The engine successfully 'tunneled' through the high complexity barrier to find the optimal solution!")
            else:
                print("\n[NOTE] The engine chose a suboptimal solution. Tuning may be required.")
                
            print("\nFull Trace:")
            print(json.dumps(result, indent=2))
        else:
             print("\n[ERROR] Engine returned failure or invalid format.")
             print(result)
    else:
        print("\n[ERROR] Mission Failed.")
        print(result_wrapper)

if __name__ == "__main__":
    run_mission()
