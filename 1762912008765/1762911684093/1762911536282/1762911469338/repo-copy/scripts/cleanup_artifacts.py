import os, re, pathlib
ART = pathlib.Path("artifacts")
if not ART.exists():
    print("No artifacts directory")
    raise SystemExit(0)
files = sorted(ART.glob("codegen_*.py"), key=lambda p: p.stat().st_mtime, reverse=True)
keep = 3
for f in files[keep:]:
    try:
        f.unlink()
    except Exception as e:
        print("Skip:", f, e)
print(f"Kept {keep}, removed {max(0, len(files)-keep)}")
