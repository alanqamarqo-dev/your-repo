
import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Volition_Engine import VolitionEngine

def test_quantum_volition():
    print("--- Testing Quantum Volition Engine ---")
    
    engine = VolitionEngine()
    
    # We want to see if it picks the "Hard but Important" goal (Structural Evolution)
    # over the "Easy but Low Value" goal (System Check).
    
    print("\nGenerating Goal using Quantum Selection...")
    goal = engine.generate_goal()
    
    print(f"\nSelected Goal: {goal['description']}")
    print(f"Type: {goal['type']}")
    
    stats = goal.get('_quantum_stats', {})
    print(f"Quantum Stats: {stats}")
    
    # Verification
    if goal['type'] == 'structural_evolution':
        print("\n✅ SUCCESS: Quantum Volition tunneled through the difficulty barrier to select the highest evolution goal.")
        print(f"Tunneling Prob: {stats.get('tunnel_prob'):.4f}")
        print(f"Importance: {stats.get('importance')}")
        print(f"Difficulty: {stats.get('difficulty')}")
    elif goal['type'] == 'maintenance':
        print("\n⚠️ NOTE: Selected Maintenance. This might happen if tunneling probability was too low.")
    else:
        print(f"\nℹ️ Selected intermediate goal: {goal['type']}")

if __name__ == "__main__":
    test_quantum_volition()
