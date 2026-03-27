import sys
import os
sys.path.insert(0, r"d:\AGL\AGL_NextGen\src")

try:
    from agl.lib.unified_lib import UnifiedLib
    print("✅ UnifiedLib loaded successfully")
except Exception as e:
    print(f"❌ Failed to load UnifiedLib: {e}")
    import traceback
    traceback.print_exc()
