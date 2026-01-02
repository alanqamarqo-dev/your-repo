import sys
import os
import json
from unittest.mock import MagicMock

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Learning_System.Self_Optimizer import quantum_update_fusion_weights

def test_quantum_optimization():
    print("🚀 Testing Quantum Self-Optimization...")
    
    # 1. Setup Mock Signals
    # Mathematical Brain is performing AMAZINGLY (High Confidence) -> Should trigger Quantum Jump
    # Code Generator is performing POORLY -> Should decrease
    signals = {
        "ohm": {"rmse": 0.01, "confidence": 0.95}, # Maps to mathematical_brain
        "poly2": {"rmse": 0.5, "confidence": 0.3}  # Maps to code_generator
    }
    
    # Initial Weights
    initial_weights = {"mathematical_brain": 1.0, "code_generator": 1.0}
    config_path = "temp_fusion_weights.json"
    with open(config_path, "w") as f:
        json.dump(initial_weights, f)
        
    print("\n📊 Input Signals:")
    print(f"  - Mathematical Brain: Confidence=0.95 (High)")
    print(f"  - Code Generator: Confidence=0.3 (Low)")
    
    # 2. Run Quantum Update
    print("\n🔮 Running Quantum Weight Update...")
    new_weights = quantum_update_fusion_weights(
        cfg_path=config_path,
        signals=signals,
        run_conf=0.96, # Very High coherence to trigger resonance
        step=0.05
    )
    
    print("\n🏆 New Weights:")
    for k, v in new_weights.items():
        change = v - initial_weights.get(k, 1.0)
        print(f"  - {k}: {v} (Change: {change:+.3f})")
        
    # 3. Verification
    math_change = new_weights["mathematical_brain"] - 1.0
    if math_change > 0.06: # Standard step is 0.05, so > 0.06 means Quantum Jump occurred
        print("\n✅ SUCCESS: Mathematical Brain received a QUANTUM JUMP in weight!")
    elif math_change > 0:
        print("\n⚠️ NOTE: Mathematical Brain increased, but maybe not a quantum jump.")
    else:
        print("\n❌ FAILURE: Mathematical Brain did not increase.")
        
    # Cleanup
    if os.path.exists(config_path):
        os.remove(config_path)

if __name__ == "__main__":
    test_quantum_optimization()
