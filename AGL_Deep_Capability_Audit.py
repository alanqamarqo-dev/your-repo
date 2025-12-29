import sys
import os
import time

# Add paths
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))
sys.path.append(os.path.join(os.getcwd(), 'AGL_Core'))
sys.path.append(os.path.join(os.getcwd(), 'AGL_Engines'))

from Core_Engines import ENGINE_SPECS, bootstrap_register_all_engines

class MockRegistry:
    def __init__(self):
        self.engines = {}
    def register(self, name, engine):
        self.engines[name] = engine
        print(f"   ✅ Registered: {name}")

def audit_capabilities():
    print("🔍 AGL DEEP CAPABILITY AUDIT")
    print("============================")
    
    registry = MockRegistry()
    
    print("\n1. Bootstrapping Engines via Central Registry...")
    # This will try to import everything defined in ENGINE_SPECS
    bootstrap_register_all_engines(registry, allow_optional=True, max_seconds=30)
    
    print("\n2. Verifying Critical Components...")
    critical_list = [
        "Heikal_Quantum_Core", 
        "Mathematical_Brain", 
        "Hive_Mind", 
        "Volition_Engine", 
        "Holographic_LLM",
        "Hosted_LLM"
    ]
    
    missing = []
    for engine_name in critical_list:
        if engine_name in registry.engines:
            print(f"   ✅ {engine_name}: ACTIVE")
        else:
            print(f"   ❌ {engine_name}: MISSING/FAILED")
            missing.append(engine_name)
            
    print("\n3. Audit Conclusion")
    if not missing:
        print("   🏆 ALL SYSTEMS GREEN. FULL ACTIVATION CONFIRMED.")
    else:
        print(f"   ⚠️ SYSTEM INCOMPLETE. Missing: {missing}")

if __name__ == "__main__":
    audit_capabilities()
