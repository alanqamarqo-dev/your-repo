import sys
import os
import time
from unittest.mock import MagicMock

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Code_Generator import CodeGenerator

def test_quantum_codegen():
    print("🚀 Testing Quantum Code Generation...")
    
    generator = CodeGenerator()
    
    # Mock LLM to avoid external dependency and ensure we get "variants"
    if generator.language_specialists['python'].llm is None:
        print("⚠️ HostedLLM not found, mocking it for test.")
        generator.language_specialists['python'].llm = MagicMock()
    
    # Setup mock responses for the 3 variants
    # 1. Standard: Simple
    # 2. Optimized: Complex but fast (High Energy, High Barrier)
    # 3. Robust: Safe
    
    def mock_chat(system, user):
        sys_lower = system.lower()
        if "standard" in sys_lower:
            return "def fib(n): return n if n<=1 else fib(n-1)+fib(n-2)"
        elif "optimized" in sys_lower:
            return """
def fib(n):
    if n < 0: raise ValueError
    if n == 0: return 0
    a, b = 0, 1
    for _ in range(n-1):
        a, b = b, a+b
    return b
""" # Longer, more complex, but faster
        elif "robust" in sys_lower:
            return """
def fib(n):
    try:
        if not isinstance(n, int): raise TypeError
        if n < 0: raise ValueError("Negative")
        # ... implementation ...
        return 0
    except Exception as e:
        print(e)
        return -1
"""
        return "print('hello')"

    generator.language_specialists['python'].llm.chat_llm = mock_chat
    
    print("\n🔮 Requesting: 'Calculate Fibonacci sequence fast'")
    # "fast" keyword should trigger resonance with "Optimized" variant
    
    result = generator.quantum_refine_code("Calculate Fibonacci sequence fast")
    
    print(f"\n🏆 Selected Variant: {result['selected_variant']}")
    print(f"   Quantum Score: {result['quantum_score']:.4f}")
    
    print("\n📊 All Variants Analysis:")
    for v in result['all_variants']:
        print(f"  - Type: {v['type']}")
        print(f"    Score: {v['score']:.4f}")
        print(f"    Metrics: {v['metrics']}")
        
    # Verification
    if result['selected_variant'] == "Optimized":
        print("\n✅ SUCCESS: Quantum Engine selected 'Optimized' code because it resonated with 'fast' requirement.")
    else:
        print(f"\n⚠️ NOTE: Selected {result['selected_variant']}. Check tuning.")

if __name__ == "__main__":
    test_quantum_codegen()
