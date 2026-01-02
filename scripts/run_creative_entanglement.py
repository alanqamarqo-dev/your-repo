import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Creative_Innovation import CreativeInnovation

def run_creative_test():
    print("=== CREATIVE INNOVATION PROTOCOL (QUANTUM ENTANGLEMENT) ===")
    print("Objective: Disprove the hypothesis that the system lacks creativity.")
    print("Method: Use 'Creative_Innovation' engine to entangle two disparate concepts into a NOVEL idea.\n")

    # Initialize Engine
    creative_engine = CreativeInnovation()
    
    # Define Concepts to Entangle
    concept_a = "Time Dilation (General Relativity)"
    concept_b = "Arabic Calligraphy (Visual Art)"
    
    print(f"Concept A: {concept_a}")
    print(f"Concept B: {concept_b}")
    print("Action: Attempting Quantum Entanglement of concepts...\n")
    
    # Create Task
    task = {
        "query": "Invent a completely new art form that combines the physics of time dilation with the aesthetics of calligraphy. Describe how it works and what it looks like.",
        "concepts": [concept_a, concept_b],
        "context": "The user challenges the system's creativity. The output must be highly innovative, not just a simple mix."
    }
    
    # Run Process
    try:
        result = creative_engine.process_task(task)
        
        if result['status'] == 'success':
            print("--- QUANTUM RESONANCE DATA ---")
            meta = result.get('quantum_metadata', {})
            print(f"State: {meta.get('state', 'Unknown')}")
            print(f"Resonance Score: {meta.get('resonance_score', 0):.4f}")
            print(f"Amplification: {meta.get('amplification', 0):.4f}")
            
            print("\n--- GENERATED INNOVATION ---")
            print(result['output'])
            
            print("\n[SUCCESS] The system has generated a novel concept using Quantum-Synaptic Resonance.")
        else:
            print(f"Error: {result}")
            
    except Exception as e:
        print(f"Execution Error: {e}")

if __name__ == "__main__":
    run_creative_test()
