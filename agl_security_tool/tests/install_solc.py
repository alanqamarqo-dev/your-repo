"""Try to download solc binary or check network availability."""
import urllib.request
import json

try:
    r = urllib.request.urlopen('https://binaries.soliditylang.org/windows-amd64/list.json', timeout=15)
    print(f"Network OK! Status: {r.status}")
    data = json.loads(r.read())
    builds = data.get('builds', [])
    for b in reversed(builds):
        ver = b['version']
        if ver.startswith('0.8.'):
            print(f"Latest 0.8.x: {ver}")
            print(f"Path: {b['path']}")
            break
except Exception as e:
    print(f"Network failed: {type(e).__name__}: {e}")

# Also try py-solc-x install
try:
    import solcx
    print("\nTrying solcx.install_solc('0.8.20')...")
    solcx.install_solc('0.8.20', show_progress=True)
    print("SUCCESS! solc 0.8.20 installed")
    print("Installed versions:", solcx.get_installed_solc_versions())
except Exception as e:
    print(f"solcx install failed: {type(e).__name__}: {e}")
