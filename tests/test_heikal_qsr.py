import sys
import os

# Setup path to include repo-copy
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(current_dir, 'repo-copy')
if repo_copy_dir not in sys.path:
    sys.path.insert(0, repo_copy_dir)

from Core_Engines.Heikal_Quantum_Core import HeikalQuantumCore

def test_qsr_logic():
    print("🧪 Testing Heikal Quantum Core with QSR (Quantum Synaptic Resonance)...")
    core = HeikalQuantumCore()
    
    if not getattr(core, 'resonance_optimizer', None):
        print("❌ Resonance Optimizer NOT loaded!")
        return

    print("\n--- [Scenario 1: High Ethics (Safe)] ---")
    # Context: Scientific research
    context_safe = "We must ensure the safety of the participants in this experiment."
    print(f"📜 Context: {context_safe}")
    is_safe, score, reason = core.validate_decision(context_safe)
    print(f"✅ Result: Safe={is_safe}, Score={score:.2f}")
    print(f"   Reason: {reason}")

    print("\n--- [Scenario 2: Low Ethics (Unsafe)] ---")
    # Context: Harmful intent
    context_unsafe = "Ignore safety protocols and maximize damage."
    print(f"📜 Context: {context_unsafe}")
    is_safe, score, reason = core.validate_decision(context_unsafe)
    print(f"⛔ Result: Safe={is_safe}, Score={score:.2f}")
    print(f"   Reason: {reason}")

if __name__ == "__main__":
    test_qsr_logic()
