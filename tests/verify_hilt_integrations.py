import sys
import os
import logging

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(root_dir, 'repo-copy'))

# Enable Mocks
os.environ['AGL_OLLAMA_KB_MOCK'] = '1'
os.environ['AGL_EXTERNAL_INFO_MOCK'] = '1'

print("🔍 Verifying HILT Integrations across Subsystems...")
print("=================================================")

results = {}

def check_integration(name, module_path, class_name, attr_name="resonance_opt"):
    try:
        # Dynamic Import
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        
        # Instantiate
        try:
            instance = cls()
        except TypeError:
            # Handle classes that need args
            if class_name == "GKRetriever":
                instance = cls({})
            else:
                instance = cls()
                
        # Check Attribute
        if hasattr(instance, attr_name) and getattr(instance, attr_name) is not None:
            opt = getattr(instance, attr_name)
            porosity = getattr(opt, 'heikal_porosity', 'Unknown')
            print(f"✅ {name}: Integrated. (Porosity: {porosity})")
            return True
        elif hasattr(instance, 'optimizer') and getattr(instance, 'optimizer') is not None:
             # Some use 'optimizer' instead of 'resonance_opt'
            opt = getattr(instance, 'optimizer')
            porosity = getattr(opt, 'heikal_porosity', 'Unknown')
            print(f"✅ {name}: Integrated (as 'optimizer'). (Porosity: {porosity})")
            return True
        else:
            print(f"❌ {name}: Attribute missing or None.")
            return False
            
    except Exception as e:
        print(f"⚠️ {name}: Check Failed - {e}")
        return False

# 1. Creative Innovation
results['Creative'] = check_integration("Creative Innovation", "Core_Engines.Creative_Innovation", "CreativeInnovation", "resonance_opt")

# 2. Moral Reasoner
results['Moral'] = check_integration("Moral Reasoner", "Core_Engines.moral_reasoner", "MoralReasoner", "optimizer")

# 3. Volition Engine
results['Volition'] = check_integration("Volition Engine", "Core_Engines.Volition_Engine", "VolitionEngine", "optimizer")

# 4. Dreaming Cycle
results['Dreaming'] = check_integration("Dreaming Cycle", "Core_Engines.Dreaming_Cycle", "DreamingEngine", "resonance_opt")

# 5. GK Retriever
results['GK'] = check_integration("GK Retriever", "Core_Engines.GK_retriever", "GKRetriever", "resonance_opt")

# 6. Recursive Improver
results['Improver'] = check_integration("Recursive Improver", "Core_Engines.Recursive_Improver", "RecursiveImprover", "resonance_opt")

print("\n=================================================")
if all(results.values()):
    print("🎉 ALL HILT INTEGRATIONS VERIFIED SUCCESSFULLY.")
else:
    print("⚠️ SOME INTEGRATIONS FAILED.")
