import time
import json
import sys
from pathlib import Path

# Ensure repo-copy is on sys.path so local packages (Core_Engines, Integration_Layer)
# are importable when running this script from the workspace root.
repo_dir = Path(__file__).resolve().parents[1]
if str(repo_dir) not in sys.path:
    sys.path.insert(0, str(repo_dir))

start = time.time()
try:
    from Core_Engines import bootstrap_register_all_engines
    from Integration_Layer.integration_registry import registry as integration_registry
    res = bootstrap_register_all_engines(integration_registry, allow_optional=True, max_seconds=60)
    status = {'registered': list(res.keys())}
except Exception as e:
    status = {'error': str(e)}
end = time.time()
print(json.dumps({'elapsed_seconds': end-start, 'status': status}, ensure_ascii=False, indent=2))
