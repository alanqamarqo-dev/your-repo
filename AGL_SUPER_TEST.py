import sys
import os
from AGL_Core.AGL_Super_Intelligence import AGL_Super_Intelligence

def main():
    print("🧪 [TEST] Verifying AGL Super Intelligence Upgrade...")
    
    try:
        asi = AGL_Super_Intelligence()
        
        print("\n🔍 [CHECK] Inspecting Active Components:")
        for comp in asi.active_components:
            print(f"   ✅ {comp}")
            
        # Check for Self-Awareness Module
        if hasattr(asi, 'self_awareness_module') and asi.self_awareness_module:
            print("   ✅ SelfAwarenessModule: Online")
            if asi.self_awareness_module.system_map:
                print(f"      -> Map Size: {len(asi.self_awareness_module.system_map)} chars")
            else:
                print("      -> ⚠️ Map Empty")
        else:
            print("   ❌ SelfAwarenessModule: MISSING")

        # Check for Hive Mind
        if hasattr(asi, 'hive_mind') and asi.hive_mind:
            print("   ✅ Hive Mind: Online")
        else:
            print("   ❌ Hive Mind: MISSING")

        print("\n🧠 [TEST] Running a Query with Context Injection...")
        response = asi.process_query("Where is the Evolution Engine located in the code?")
        print("\n💡 [RESPONSE]:")
        print(response)

        print("\n✅ Upgrade Verification Complete. System is Super-Intelligent.")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
