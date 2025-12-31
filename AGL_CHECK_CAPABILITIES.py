import sys
import os
import importlib.util
import inspect

# Add current directory to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "repo-copy"))

def check_capabilities():
    print("🔍 Checking AGL_Awakened.py Capabilities...")
    
    try:
        from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
        asi = AGL_Super_Intelligence()
        
        # Define expected capabilities based on the file content
        expected_caps = {
            "core": "HeikalQuantumCore",
            "volition": "VolitionEngine",
            "math_brain": "MathematicalBrain",
            "hive_mind": "HiveMind",
            "self_awareness": "SelfAwarenessModule",
            "causal_engine": "CausalGraphEngine",
            "strategist": "StrategicThinkingEngine",
            "learner": "SelfLearning",
            "focus_controller": "SmartFocusController",
            "meta_cognition": "MetaCognitionEngine",
            "recursive_improver": "RecursiveImprover",
            "neural_bridge": "NeuralResonanceBridge",
            "holo_projector": "HolographicRealityProjector",
            "reasoning_planner": "ReasoningPlanner",
            "hypothesis_generator": "HypothesisGeneratorEngine",
            "counterfactual_explorer": "CounterfactualExplorer",
            "meta_learner": "MetaLearningEngine",
            "unified_system": "UnifiedAGISystem"
        }
        
        print("\n📊 Capability Status Report:")
        print(f"{'Capability':<30} | {'Status':<10} | {'Type/Value':<30}")
        print("-" * 75)
        
        all_active = True
        
        for attr, expected_type in expected_caps.items():
            if hasattr(asi, attr):
                val = getattr(asi, attr)
                if val is not None:
                    status = "✅ Active"
                    type_name = type(val).__name__
                else:
                    status = "❌ Inactive"
                    type_name = "None"
                    all_active = False
            else:
                status = "❓ Missing"
                type_name = "Attribute Not Found"
                all_active = False
                
            print(f"{attr:<30} | {status:<10} | {type_name:<30}")
            
        # Check Engine Registry specifically for the placeholders
        print("\n🧩 Engine Registry Check (Placeholders):")
        registry = getattr(asi, 'engine_registry', {})
        placeholders = ['Creative_Innovation', 'Self_Reflective', 'Reasoning_Layer']
        for p in placeholders:
            val = registry.get(p)
            status = "✅ Active" if val else "⚠️ Inactive (Placeholder)"
            print(f"  - {p}: {status}")

        if all_active:
            print("\n✨ ALL PRIMARY CAPABILITIES ARE ACTIVE.")
        else:
            print("\n⚠️ SOME CAPABILITIES ARE INACTIVE OR MISSING.")

    except Exception as e:
        print(f"❌ Error during check: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_capabilities()
