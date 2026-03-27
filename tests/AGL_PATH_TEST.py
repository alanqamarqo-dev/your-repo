import sys
import os

print("🚀 Starting Path Integration Test...")
print(f"📂 Current Working Directory: {os.getcwd()}")

# 1. Bootstrap: Try to import the Unified Interface
# This should trigger AGL_Paths to configure sys.path
try:
    from AGL_Core.AGL_Unified_Python import UnifiedLib
    print("✅ [Bootstrap] AGL_Unified_Python loaded successfully.")
except ImportError as e:
    print(f"❌ [Bootstrap] Failed to load AGL_Unified_Python: {e}")
    # Attempt manual fix for test purposes if bootstrap fails
    sys.path.append(os.path.join(os.getcwd(), 'AGL_Core'))
    try:
        from AGL_Unified_Python import UnifiedLib
        print("   ⚠️ [Bootstrap] Loaded via fallback path append.")
    except:
        sys.exit(1)

# 2. Test Imports from various layers
# These rely on AGL_Paths having added 'repo-copy', 'Core_Engines', etc. to sys.path
modules_to_test = [
    ("AGL_Core.Heikal_Quantum_Core", "HeikalQuantumCore"),       # Core Layer (Class)
    ("Core_Engines.Hosted_LLM", "HostedLLM"),                   # Repo-Copy / Core Engines (Class)
    ("Integration_Layer.Hybrid_Composer", "build_prompt_context"), # Repo-Copy / Integration (Function)
    ("Safety_Systems.Dissonance_Watchdog", "DissonanceWatchdog"), # Repo-Copy / Safety (Class)
]

print("\n🧪 Testing Cross-Module Visibility:")
success_count = 0
for module_path, class_name in modules_to_test:
    try:
        # Dynamic import
        mod = __import__(module_path, fromlist=[class_name])
        # Check if class exists
        if hasattr(mod, class_name):
            print(f"   ✅ Imported {class_name} from {module_path}")
            success_count += 1
        else:
             print(f"   ⚠️ Imported {module_path} but {class_name} not found.")
    except ImportError as e:
        print(f"   ❌ Failed to import {module_path}: {e}")
    except Exception as e:
        print(f"   ❌ Error importing {module_path}: {e}")

print(f"\n📊 Result: {success_count}/{len(modules_to_test)} modules imported successfully.")

if success_count == len(modules_to_test):
    print("🎉 SYSTEM PATHS ARE FULLY UNIFIED!")
else:
    print("⚠️ Some paths are still broken.")
