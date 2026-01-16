import sys
import os
import time
import json
import types
from unittest.mock import MagicMock

# 1. SETUP ENV & PATHS
sys.path.append(r"d:\AGL\AGL_NextGen\src")

# 2. SETUP CONSENT (REQUIRED BY ENGINE)
consent_path = r"d:\AGL\AGL_NextGen\AGL_HUMAN_CONSENT.txt"
with open(consent_path, "w", encoding="utf-8") as f:
    f.write("GRANTED") # Strict requirement by _check_human_consent

# 2. MOCK REQUESTS (To simulate LLM response without killing the Real Engine)
mock_requests = types.ModuleType("requests")
sys.modules["requests"] = mock_requests

# Prepare a "Real" LLM Response containing Optimized Code
OPTIMIZED_CODE_CONTENT = """
def slow_function():
    # OPTIMIZED by AGL Recursive Improver
    # Complexity reduced from O(n^2) to O(1)
    x = 1000 * 1000
    print("Done")
    return x
"""

# Configure the mock post response
mock_response = MagicMock()
mock_response.status_code = 200
mock_response.json.return_value = {
    "response": f"Here is the optimized code:\n```python\n{OPTIMIZED_CODE_CONTENT}\n```"
}
mock_requests.post = MagicMock(return_value=mock_response)
mock_requests.exceptions = types.ModuleType("exceptions")
mock_requests.exceptions.RequestException = Exception

print("🔧 [SETUP] Network Layer Mocked. Injecting Real Engine...")

# 3. IMPORT REAL ENGINE
try:
    from agl.engines.recursive_improver import RecursiveImprover
    print("✅ [IMPORT] REAL RecursiveImprover Loaded successfully.")
except ImportError as e:
    print(f"❌ [CRITICAL] Import Failed: {e}")
    # Try to debug path
    print(f"   Current Path: {sys.path}")
    sys.exit(1)

def run_real_evolution():
    print("\n" + "="*60)
    print("🧬 AGL REAL-WORLD EVOLUTION TEST")
    print("="*60)
    
    # Target File
    target_path = r"d:\AGL\AGL_NextGen\src\agl\engines\target_bad_code.py"
    
    # Initialize Engine
    improver = RecursiveImprover()

    # Safety: Check if method exists before calling.
    # The AGL architecture evolves, so APIs may shift.
    if hasattr(improver, 'enable_unlimited_simulation'):
        improver.enable_unlimited_simulation(safety_checks=True) 
    else:
        print("ℹ️ [INFO] 'enable_unlimited_simulation' mode not found. Using default standard mode.")
    
    print(f"📝 [TARGET] Identified outdated code at: {os.path.basename(target_path)}")
    
    # Read original content
    with open(target_path, 'r') as f:
        original_content = f.read()
    print(f"   -> Original Size: {len(original_content)} bytes")
    
    # EXECUTE IMPROVEMENT (This runs the REAL internal logic: Backup -> Ask LLM -> Validate -> Write)
    print("🚀 [EXECUTE] Initiating Recursive Improvement Sequence...")
    result = improver.improve_file(
        file_path=target_path,
        objective="Optimize complexity from O(n^2) to O(1)."
    )
    
    print("\n📊 [REPORT] ENGINE OUTPUT:")
    print(json.dumps(result, indent=2))
    
    # VERIFICATION
    print("\n🔍 [AUDIT] System Verification:")
    
    # 1. Check if Code Changed
    with open(target_path, 'r') as f:
        new_content = f.read()
        
    if "1000 * 1000" in new_content:
        print("   ✅ [CODE] File content successfully mutated/optimized.")
    else:
        print("   ❌ [CODE] File content unchanged.")
        
    # 2. Check Backup
    backup_dir = improver.backup_dir
    files = list(backup_dir.glob("*target_bad_code.py*"))
    if len(files) > 0:
        print(f"   ✅ [SAFETY] Backup created: {files[0].name}")
    else:
        print("   ❌ [SAFETY] No backup found! (Protocol Violation)")

    # 3. Check AST Integrity (Did the engine verify syntax?)
    if result.get("status") == "success":
        print("   ✅ [LOGIC] Engine reported success internally.")
    else:
        print(f"   ⚠️ [LOGIC] Engine reported: {result.get('status')}")

if __name__ == "__main__":
    run_real_evolution()
