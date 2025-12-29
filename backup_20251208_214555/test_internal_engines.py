#!/usr/bin/env python3
"""اختبار المحركات الداخلية مباشرة"""

import requests
import json

def test_math_engine():
    """اختبار محرك الرياضيات"""
    print("\n🧮 اختبار MathematicalBrain:")
    
    test_cases = [
        "2x + 5 = 13",
        "solve: 3x - 7 = 20",
        "calculate: 15 + 27 * 3"
    ]
    
    for case in test_cases:
        try:
            response = requests.post(
                "http://127.0.0.1:8000/chat",
                json={"message": case},
                timeout=10
            )
            result = response.json()
            print(f"  ✓ {case}")
            print(f"    → {result.get('reply', 'No reply')[:100]}")
            print(f"    → Engine: {result.get('meta', {}).get('engine', 'Unknown')}")
        except Exception as e:
            print(f"  ✗ {case}: {e}")

def test_simulation_engine():
    """اختبار محرك المحاكاة"""
    print("\n🔬 اختبار AdvancedSimulationEngine:")
    
    test_cases = [
        "simulate quantum thermodynamic process",
        "run metric tensor simulation",
        "simulate entropy reversal"
    ]
    
    for case in test_cases:
        try:
            response = requests.post(
                "http://127.0.0.1:8000/chat",
                json={"message": case},
                timeout=10
            )
            result = response.json()
            print(f"  ✓ {case}")
            reply = result.get('reply', 'No reply')
            if len(reply) > 200:
                print(f"    → {reply[:200]}...")
            else:
                print(f"    → {reply}")
            print(f"    → Engine: {result.get('meta', {}).get('engine', 'Unknown')}")
        except Exception as e:
            print(f"  ✗ {case}: {e}")

def test_direct_import():
    """اختبار الاستيراد المباشر"""
    print("\n🔧 اختبار الاستيراد المباشر:")
    
    try:
        from Core_Engines.Mathematical_Brain import MathematicalBrain
        brain = MathematicalBrain()
        result = brain.process_task("2x + 5 = 13")
        print(f"  ✅ MathematicalBrain: {result}")
    except Exception as e:
        print(f"  ❌ MathematicalBrain: {e}")
    
    try:
        import importlib.util
        import os
        spec = importlib.util.spec_from_file_location(
            'tmp_advanced_simulator',
            os.path.join(os.path.dirname(__file__), 'tmp_advanced_simulator.py')
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sim = module.AdvancedSimulationEngine()
        result = sim.run_quantum_thermo({'steps': 10, 'dt': 0.01})
        print(f"  ✅ AdvancedSimulationEngine: {len(result.get('time', []))} time points")
    except Exception as e:
        print(f"  ❌ AdvancedSimulationEngine: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("🧪 اختبار المحركات الداخلية القوية")
    print("=" * 60)
    
    test_direct_import()
    test_math_engine()
    test_simulation_engine()
    
    print("\n" + "=" * 60)
    print("✅ الاختبار انتهى")
    print("=" * 60)
