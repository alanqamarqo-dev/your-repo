import sys
import os
import importlib.util

# Add repo-copy to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'repo-copy'))

def verify_server_integration():
    print("🔍 Verifying Server Integration...")
    
    # We want to check if the UnifiedAGISystem used by server_fixed.py has the clusters
    # We can't easily run the full server, but we can import the module it uses.
    
    try:
        from dynamic_modules.unified_agi_system import UnifiedAGISystem
        
        # Instantiate a dummy system
        system = UnifiedAGISystem({})
        
        if hasattr(system, 'engine_clusters'):
            print("✅ UnifiedAGISystem (used by server) has 'engine_clusters'.")
            print(f"   Clusters: {list(system.engine_clusters.keys())}")
        else:
            print("❌ UnifiedAGISystem MISSING 'engine_clusters'.")
            
    except ImportError as e:
        print(f"❌ Failed to import UnifiedAGISystem: {e}")

if __name__ == "__main__":
    verify_server_integration()
