import sys
import os
import time

# Add repo root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'repo-copy'))

from Core_Engines.Dreaming_Cycle import DreamingEngine

def test_dreaming_cycle():
    print("🧪 Testing Dreaming Cycle...")
    
    engine = DreamingEngine()
    
    # 1. Add some mock memories
    print("   - Adding mock memories...")
    engine.add_to_buffer("User asked to calculate pi to 100 digits. I used the math module.")
    engine.add_to_buffer("Encountered an error in file read operation. Retried and succeeded.")
    engine.add_to_buffer("Optimized the search algorithm, reduced latency by 15%.")
    
    # 2. Run Cycle
    print("   - Running dream cycle...")
    results = engine.run_dream_cycle(duration_seconds=30)
    
    # 3. Verify Results
    print("\n📊 Results:")
    for res in results:
        print(f"   - {res}")
        
    # 4. Check KB file
    kb_path = engine.knowledge_base_path
    if os.path.exists(kb_path):
        print(f"\n✅ Knowledge Base file exists at: {kb_path}")
        with open(kb_path, 'r', encoding='utf-8') as f:
            data = f.read()
            print(f"   KB Size: {len(data)} bytes")
    else:
        print("\n❌ Knowledge Base file not found!")

if __name__ == "__main__":
    test_dreaming_cycle()
