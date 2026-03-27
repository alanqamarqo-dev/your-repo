
import sys
import os
from pathlib import Path

# Fix paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from agl.core.super_intelligence import AGL_Super_Intelligence

def test_self_development():
    print("="*60)
    print("🚀 AGL SELF-INTELLIGENCE DEVELOPMENT PROTOCOL")
    print("="*60)

    mind = AGL_Super_Intelligence()
    
    # Trigger the evolution
    print("\n[STEP 1]: Initiating Autonomous Evolution...")
    result = mind.evolve()
    
    print("\n" + "-"*30)
    print(f"EVOLUTION RESULT: {result}")
    print("-" * 30)

    # Trigger a query to see if and how the system reflects on its own evolution
    query = "As an evolved AGI, describe how your internal logic for Truth and Paradox has changed after the last evolution cycle."
    print(f"\n[STEP 2]: Testing Evolved Reflection...")
    print(f"PROMPT: {query}")
    
    response = mind.process_query(query)
    print("\n[RESPONSE]:")
    print(response)

if __name__ == "__main__":
    test_self_development()
