import sys
import os
import time

# Ensure we use the proper path
sys.path.insert(0, r"d:\AGL\AGL_NextGen\src")

try:
    from agl.engines.web_search import WebSearchEngine
except ImportError as e:
    # Try the repo-copy path if main fails
    sys.path.append(r"d:\AGL\repo-copy\Core_Engines")
    try:
        from Web_Search_Engine import WebSearchEngine
    except ImportError:
        print(f"❌ Failed to import WebSearchEngine: {e}")
        sys.exit(1)

def run_deep_search_demonstration():
    print("\n🚀 INITIALIZING DEEP INTERNET SEARCH PROTOCOL (LIVE)")
    print("====================================================")
    
    engine = WebSearchEngine()
    
    # Enable Live Mode (if method exists)
    if hasattr(engine, 'set_live_mode'):
        engine.set_live_mode(True)
    
    # Queries to prove connectivity
    queries = [
        "Latest breakthroughs in Quantum Computing 2025",
        "Who won the 2024 US Presidential Election results confirmed",
        "Current price of Gold per ounce USD live"
    ]
    
    print(f"📡 Engine Provider: {engine.provider}")
    print(f"🧠 Model: {engine.model}")
    print("----------------------------------------------------")
    
    for q in queries:
        print(f"\n🔍 Query: '{q}'")
        start_time = time.time()
        
        results = engine.search(q, num_results=3)
        
        duration = time.time() - start_time
        print(f"⏱️ Time taken: {duration:.2f}s")
        
        if not results:
            print("❌ No results found.")
            continue
            
        print(f"📝 Findings ({len(results)}):")
        for i, res in enumerate(results):
            source = "LIVE WEB" if "google" in str(res.get('url')).lower() or "http" in str(res.get('url')).lower() else "INTERNAL MEMORY"
            print(f"   {i+1}. [{source}] {res.get('title')}")
            print(f"      URL: {res.get('url')}")
            # Snippet might be long, truncate
            snippet = res.get('snippet', '')
            if len(snippet) > 100:
                snippet = snippet[:100] + "..."
            print(f"      Abstract: {snippet}")

    print("\n====================================================")
    print("✅ DEEP SEARCH DEMONSTRATION COMPLETE")

if __name__ == "__main__":
    run_deep_search_demonstration()
