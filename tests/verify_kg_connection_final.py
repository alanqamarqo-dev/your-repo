import sys
import os

# Setup paths
current_dir = os.getcwd()
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "repo-copy"))

print("🧪 Verifying PERMANENT Connection: Knowledge Graph <-> Scientific Systems")
print("======================================================================")

try:
    # Load Scientific Orchestrator
    from Scientific_Systems.Scientific_Integration_Orchestrator import ScientificIntegrationOrchestrator
    
    print("Instantiating ScientificIntegrationOrchestrator...")
    orchestrator = ScientificIntegrationOrchestrator()
    
    # Check connection
    from Self_Improvement.Knowledge_Graph import KnowledgeNetwork
    
    if isinstance(orchestrator.knowledge_base, KnowledgeNetwork):
        print("\n✅ SUCCESS: Orchestrator automatically initialized with KnowledgeNetwork!")
        print(f"   Type: {type(orchestrator.knowledge_base)}")
    else:
        print("\n❌ FAILURE: Orchestrator still using dictionary or other type.")
        print(f"   Type: {type(orchestrator.knowledge_base)}")

except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Runtime Error: {e}")
