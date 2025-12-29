import os

# القيم المطلوب تعديلها
target_file = r"D:\AGL\repo-copy\Core_Engines\Quantum_Neural_Core.py"
print(f"repairing: {target_file}...")

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

patch_code = """
import torch
# --- CRITICAL PATCH START ---
# Fix for missing complex64 in older torch versions
if not hasattr(torch, 'complex64'):
    print("⚠️ Patching torch.complex64 support...")
    torch.complex64 = torch.float32
    try:
        import numpy as np
        torch.complex64 = torch.from_numpy(np.array([], dtype=np.complex64)).dtype
    except Exception:
        pass
# --- CRITICAL PATCH END ---
"""

if "import torch" in content and "CRITICAL PATCH START" not in content:
    new_content = content.replace("import torch", "import torch" + patch_code, 1)
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Fix applied successfully. The brain should load now.")
else:
    print("ℹ️ File already patched or 'import torch' not found.")
