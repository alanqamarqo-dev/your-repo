import sys
import os

# Setup paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'repo-copy'))

from Integration_Layer.Quantum_Action_Router import QuantumActionRouter

def main():
    print("\n🌌 --- QUANTUM RESONANCE ROUTER DEMO --- 🌌")
    print("This tool demonstrates how the system uses Quantum Tunneling logic")
    print("to select the best handler for a task based on 'Vibrational Match'.\n")
    
    router = QuantumActionRouter()
    
    while True:
        user_input = input("\nEnter a task (or 'exit'): ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        print(f"\n🔍 Analyzing Resonance for: '{user_input}'...")
        
        result = router.route(user_input)
        
        print(f"\n🏆 WINNER: {result['selected_handler'].upper()}")
        print(f"   Resonance Score: {result['resonance_score']:.6f}")
        
        print("\n📊 Full Spectrum Analysis:")
        for item in result['all_scores']:
            bar_len = int(item['resonance'] * 100000) # Scale for visibility
            bar = "█" * min(bar_len, 20)
            print(f"   - {item['handler']:<15}: {item['resonance']:.6f} {bar}")

if __name__ == "__main__":
    main()
