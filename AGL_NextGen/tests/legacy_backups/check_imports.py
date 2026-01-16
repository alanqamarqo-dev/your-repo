import sys
import os

# Setup Path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, "AGL_NextGen", "src")
sys.path.insert(0, src_path)

print(f"Checking imports from: {src_path}")

try:
    import agl.core.super_intelligence as si
    print(f"✅ Imported: {si}")
    print(f"📂 File: {si.__file__}")
    
    # Read lines 360-380 from the file
    with open(si.__file__, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print("\n--- CONTENT OF LINE 360-380 ---")
        for i, line in enumerate(lines[360:380], 361):
            print(f"{i}: {line.strip()}")
        print("-------------------------------")

except Exception as e:
    print(f"❌ Failed to import: {e}")
