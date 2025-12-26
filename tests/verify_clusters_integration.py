import sys
import os
import json

# Add repo-copy to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'repo-copy'))

try:
    from dynamic_modules.unified_agi_system import UnifiedAGISystem
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from repo_copy.dynamic_modules.unified_agi_system import UnifiedAGISystem # type: ignore

def verify_clusters():
    print("🔄 Initializing Unified AGI System for Cluster Verification...")
    # Initialize with empty registry
    system = UnifiedAGISystem(engine_registry={})
    
    print("\n🔍 Checking Engine Clusters Integration...")
    
    if hasattr(system, 'engine_clusters'):
        print("✅ 'engine_clusters' attribute found.")
        clusters = system.engine_clusters
        print(f"📊 Found {len(clusters)} clusters: {list(clusters.keys())}")
        
        # Verify specific cluster content
        if "creative_writing" in clusters:
            print("   - creative_writing: OK")
            print(f"     Primary: {clusters['creative_writing']['primary']}")
        else:
            print("   ❌ creative_writing cluster missing!")
            
    else:
        print("❌ 'engine_clusters' attribute NOT found!")
        return

    print("\n🔍 Checking Helper Method 'get_cluster_engines'...")
    if hasattr(system, 'get_cluster_engines'):
        print("✅ 'get_cluster_engines' method found.")
        
        engines = system.get_cluster_engines("scientific_reasoning")
        print(f"   - Scientific Reasoning Engines: {len(engines)} found.")
        print(f"   - Sample: {engines[:3]}...")
        
        if len(engines) > 0:
            print("✅ Helper method works correctly.")
        else:
            print("❌ Helper method returned empty list.")
    else:
        print("❌ 'get_cluster_engines' method NOT found!")

if __name__ == "__main__":
    verify_clusters()
