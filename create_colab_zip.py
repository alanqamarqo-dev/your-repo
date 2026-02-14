"""
Creates a minimal ZIP file for uploading to Google Colab.
Only includes: agl_security_tool/ + test_project/
Run: python create_colab_zip.py
"""
import zipfile, os

ZIP_NAME = "agl_upload.zip"
INCLUDE = ["agl_security_tool", "test_project"]

with zipfile.ZipFile(ZIP_NAME, 'w', zipfile.ZIP_DEFLATED) as zf:
    count = 0
    for folder in INCLUDE:
        for root, dirs, files in os.walk(folder):
            # Skip __pycache__ and .git
            dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', 'node_modules')]
            for f in files:
                if f.endswith(('.pyc', '.pyo')):
                    continue
                path = os.path.join(root, f)
                zf.write(path, path)
                count += 1

size_mb = os.path.getsize(ZIP_NAME) / 1024**2
print(f"✅ Created {ZIP_NAME}: {count} files, {size_mb:.1f} MB")
print(f"📤 Upload this file to Colab when prompted")
