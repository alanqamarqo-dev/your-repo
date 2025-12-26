
import sys
import os
import time

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
sys.path.append(root_dir)
sys.path.append(repo_copy_dir)

from Core_Engines.GK_retriever import GKRetriever

# Mock KB Adapter
class MockKB:
    def search_text(self, text, top_k=10):
        # Simulate results with varying relevance scores
        return [
            {"id": "doc1", "content": "Exact match for query", "_score": 0.95},
            {"id": "doc2", "content": "Relevant but different words", "_score": 0.7},
            {"id": "doc3", "content": "Somewhat related", "_score": 0.4}, # Barrier
            {"id": "doc4", "content": "Hidden gem (low score but resonant)", "_score": 0.35}, # Tunnel candidate
            {"id": "doc5", "content": "Irrelevant noise", "_score": 0.1}
        ]

def test_resonant_retrieval():
    print("\n🧠 Testing Resonant Memory Retrieval...")
    
    # Setup Retriever with Mock KB
    adapters = {"local": MockKB()}
    retriever = GKRetriever(adapters)
    
    class Query:
        text = "test query"
        
    # Run Retrieval
    results = retriever.retrieve(Query())
    
    print(f"   Retrieved {len(results)} items.")
    
    # Analyze Results
    ids = [item.get('id') for item in results]
    print(f"   Result IDs: {ids}")
    
    # Check if the "Hidden gem" (doc4) survived or got boosted
    # In standard retrieval, doc4 (0.35) might be cut off if limit is small, 
    # but here we check if it's present and potentially re-ordered.
    
    if "doc4" in ids:
        print("   ✅ Quantum Tunneling Successful! (Hidden gem retrieved)")
    else:
        print("   ⚠️ Hidden gem not retrieved (might be too low energy).")
        
    # Check if noise was filtered (doc5 is very low)
    if "doc5" not in ids:
         print("   ✅ Noise Filtering Successful!")
    elif ids.index("doc5") > ids.index("doc1"):
         print("   ✅ Ranking preserved (Noise is last).")

if __name__ == "__main__":
    test_resonant_retrieval()
