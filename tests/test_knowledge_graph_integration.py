import sys
import os

# Setup paths like AGL_Awakened.py
current_dir = os.getcwd()
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "repo-copy"))

print(f"Testing Knowledge Graph Integration...")
print(f"Sys path includes: {sys.path[-2:]}")

try:
    from Self_Improvement.Knowledge_Graph import KnowledgeNetwork
    print("✅ Direct import of KnowledgeNetwork successful.")
except ImportError as e:
    print(f"❌ Direct import failed: {e}")

try:
    from AGL_Core.Heikal_Quantum_Core import HeikalQuantumCore
    print("✅ HeikalQuantumCore imported.")
    
    # Instantiate Core
    print("Instantiating HeikalQuantumCore...")
    core = HeikalQuantumCore()
    
    if hasattr(core, 'knowledge_graph') and core.knowledge_graph is not None:
        print(f"✅ core.knowledge_graph is initialized: {type(core.knowledge_graph)}")
        print("Integration successful!")
    else:
        print("❌ core.knowledge_graph is NOT initialized.")
        
except ImportError as e:
    print(f"❌ HeikalQuantumCore import failed: {e}")
except Exception as e:
    print(f"❌ Error during instantiation: {e}")
