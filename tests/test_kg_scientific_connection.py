import sys
import os

# Setup paths
current_dir = os.getcwd()
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "repo-copy"))

print("🧪 Testing Connection: Knowledge Graph <-> Scientific Systems")
print("===========================================================")

try:
    # 1. Load Knowledge Graph
    from Self_Improvement.Knowledge_Graph import KnowledgeNetwork
    kg = KnowledgeNetwork()
    print("✅ Knowledge Graph Loaded.")
    
    # 2. Load Scientific Orchestrator
    from Scientific_Systems.Scientific_Integration_Orchestrator import ScientificIntegrationOrchestrator
    orchestrator = ScientificIntegrationOrchestrator()
    print("✅ Scientific Orchestrator Loaded.")
    
    # 3. Check for existing connection
    print("\n🔍 Checking for pre-existing connection...")
    if isinstance(orchestrator.knowledge_base, KnowledgeNetwork):
        print("   ✅ CONNECTED: Orchestrator already uses KnowledgeNetwork.")
    elif orchestrator.knowledge_base == {}:
        print("   ❌ DISCONNECTED: Orchestrator uses an empty dict placeholder.")
    else:
        print(f"   ❓ UNKNOWN: Orchestrator uses {type(orchestrator.knowledge_base)}")

    # 4. Attempt Manual Integration
    print("\n🔗 Attempting Manual Integration...")
    orchestrator.knowledge_base = kg
    print("   ✅ Injected Knowledge Graph into Orchestrator.")
    
    # 5. Verify Integration works
    print("\n🧪 Verifying Integration...")
    # Add a scientific engine/concept to KG using correct methods
    kg.add_engine("Physics_Engine", ["Energy", "Mass", "Relativity"], perf_score=0.9)
    kg.add_engine("Math_Engine", ["Calculus", "Algebra"], perf_score=0.8)
    kg.connect("Physics_Engine", "Math_Engine", weight=0.5)
    
    # Check if Orchestrator can 'see' it
    if "Physics_Engine" in orchestrator.knowledge_base.nodes:
        print("   ✅ SUCCESS: Orchestrator can access 'Physics_Engine' node from Knowledge Graph.")
        print(f"   📊 Node Data: {orchestrator.knowledge_base.nodes['Physics_Engine']}")
    else:
        print("   ❌ FAILURE: Orchestrator cannot access data.")

except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Runtime Error: {e}")
