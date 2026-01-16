import sys
import os

# Set up paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from agl.core.super_intelligence import AGL_Super_Intelligence

def test_web_bridge():
    print("="*60)
    print("🌍 TESTING LIVE WEB SEARCH BRIDGE")
    print("="*60)
    
    # Initialize ASI
    asi = AGL_Super_Intelligence()
    
    # Enable capabilities
    asi.enable_super_intelligence_capabilities(
        recursive_improvement=False,
        live_knowledge=True, # Activation target
        deep_causal=False
    )

    web_engine = asi.engine_registry.get("Web_Search_Engine")
    
    if web_engine:
        print("\n🕸️ [Web] Search Engine Found. Querying real-time internet context...")
        query = "What is the latest world breaking news today 2025?"
        print(f"   -> Query: {query}")
        
        result = web_engine.process_task(query)
        
        print("\n🔍 [RESULT]:")
        if "results" in result:
             for i, res in enumerate(result['results'][:3]):
                  print(f"   [{i+1}] {res.get('title')}")
                  print(f"       {res.get('snippet')[:100]}...")
        else:
             print(f"   {result.get('note', 'No data returned.')}")
        
        print("\n✅ WEB BRIDGE TEST COMPLETED.")
        
    else:
        print("\n❌ [Web] Error: Web Search Engine not found in registry.")

if __name__ == "__main__":
    test_web_bridge()
