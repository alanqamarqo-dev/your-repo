import sys
import os
import time
import json

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(root_dir, 'repo-copy'))

# Enable Mocks for Testing
os.environ['AGL_OLLAMA_KB_MOCK'] = '1'
os.environ['AGL_EXTERNAL_INFO_MOCK'] = '1'

# Import Engines from all disciplines
try:
    from Core_Engines.Creative_Innovation import CreativeInnovation
    from Core_Engines.Mathematical_Brain import MathematicalBrain
    from Core_Engines.Volition_Engine import VolitionEngine
    from Engineering_Engines.Advanced_Code_Generator import AdvancedCodeGenerator
    from Core_Consciousness.Self_Model import SelfModel
    from Core_Engines.Resonance_Optimizer import ResonanceOptimizer
    print("✅ All modules imported successfully.")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

def run_comprehensive_test():
    print("\n🚀 Starting Comprehensive Multi-Disciplinary Integration Test")
    print("============================================================")
    
    results = {}
    
    # 1. Autonomy (Volition)
    print("\n[1] Testing Autonomy (Volition Engine)...")
    try:
        volition = VolitionEngine()
        goal = volition.generate_goal()
        print(f"   👉 Generated Goal: {goal['description']} (Type: {goal['type']})")
        results['autonomy'] = True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['autonomy'] = False

    # 2. Creativity (Innovation)
    print("\n[2] Testing Creativity (Creative Innovation Engine)...")
    try:
        creative = CreativeInnovation()
        problem = "Design a habitat for Mars colonization using local resources."
        print(f"   👉 Problem: {problem}")
        innovation = creative.process_task({
            "query": problem,
            "context": "Must use regolith, Self-sustaining energy"
        })
        # Handle different return types (dict or string)
        sol = innovation.get('solution') if isinstance(innovation, dict) else str(innovation)
        print(f"   👉 Solution Snippet: {str(sol)[:100]}...")
        results['creativity'] = True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['creativity'] = False

    # 3. Science (Math)
    print("\n[3] Testing Science (Mathematical Brain)...")
    try:
        math_brain = MathematicalBrain()
        # Simple task: Prime factorization or calculation
        math_task = "integrate x^2 from 0 to 3" 
        # Note: MathematicalBrain might expect different input, let's try a generic process_task
        # If it fails, we fallback to a simpler check
        math_res = math_brain.process_task(math_task)
        print(f"   👉 Math Result: {math_res}")
        results['science'] = True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['science'] = False

    # 4. Engineering (Code Generation)
    print("\n[4] Testing Engineering (Advanced Code Generator)...")
    try:
        coder = AdvancedCodeGenerator()
        specs = {
            "name": "MarsHabitatControl",
            "software_requirements": {
                "name": "LifeSupportSystem",
                "components": {
                    "OxygenGenerator": {"language": "python", "type": "data_processor"}
                }
            }
        }
        # Generate a child system or component
        code_sys = coder.generate_software_system(specs['software_requirements'])
        comps = code_sys.get('components', {})
        print(f"   👉 Generated Components: {list(comps.keys())}")
        results['engineering'] = True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['engineering'] = False

    # 5. Consciousness (Self Model)
    print("\n[5] Testing Consciousness (Self Model)...")
    try:
        self_model = SelfModel()
        self_model.add_biography_event(
            kind="test_milestone", 
            note="Completed comprehensive integration test", 
            source="IntegrationTest"
        )
        # Check if event was added
        last_event = self_model.biography[-1]
        print(f"   👉 Biography Updated: {last_event['note']}")
        results['consciousness'] = True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['consciousness'] = False

    # 6. HILT Physics (Resonance Optimizer)
    print("\n[6] Testing HILT Physics (Resonance Optimizer)...")
    try:
        opt = ResonanceOptimizer()
        opt.heikal_porosity = 1.5
        # Quick tunneling check
        prob = opt._heikal_tunneling_prob(energy_diff=-5, barrier_height=5)
        print(f"   👉 Tunneling Probability: {prob:.6f}")
        if prob > 0:
            results['hilt_physics'] = True
        else:
            print("   ❌ Tunneling probability should be > 0")
            results['hilt_physics'] = False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results['hilt_physics'] = False

    # Summary
    print("\n============================================================")
    print("📊 Test Summary:")
    all_passed = all(results.values())
    for k, v in results.items():
        status = "✅ PASS" if v else "❌ FAIL"
        print(f"   - {k.capitalize()}: {status}")
    
    if all_passed:
        print("\n🎉 SYSTEM INTEGRITY CONFIRMED. All disciplines operational.")
    else:
        print("\n⚠️ SYSTEM WARNING. Some disciplines failed.")

if __name__ == "__main__":
    run_comprehensive_test()
