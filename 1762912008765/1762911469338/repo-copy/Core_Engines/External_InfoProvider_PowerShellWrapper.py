import os
import subprocess
import shlex
from typing import Dict, Any, Optional

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tools', 'launch_live.ps1')


def ensure_env_for_live(model: Optional[str] = None, openai_key: Optional[str] = None):
    """Set environment variables in the current process so Python callers can
    use the ExternalInfoProvider without requiring the user to run the PS1 script.

    This does not execute launch_live.ps1; it mirrors the env toggles it sets.
    """
    if openai_key:
        os.environ['OPENAI_API_KEY'] = openai_key
    os.environ['AGL_EXTERNAL_INFO_ENABLED'] = '1'
    if model:
        os.environ['AGL_EXTERNAL_INFO_MODEL'] = model
    # ensure mock is unset so provider uses real API
    os.environ['AGL_EXTERNAL_INFO_MOCK'] = ''


def run_launch_live(dry_run: bool = True, clear_cache: bool = False, harvest_count: int = 1, start_server: bool = False) -> Dict[str, Any]:
    """Invoke the PowerShell `launch_live.ps1` script in a subprocess.

    Returns a dict with {ok, rc, stdout, stderr}.
    """
    if not os.path.exists(SCRIPT_PATH):
        return {"ok": False, "error": "launch_live.ps1 not found", "path": SCRIPT_PATH}

    args = [SCRIPT_PATH]
    if dry_run:
        args.append('-DryRun')
    if clear_cache:
        args.append('-ClearCache')
    if harvest_count and harvest_count > 1:
        args.extend(['-HarvestCount', str(harvest_count)])
    if start_server:
        args.append('-StartServer')

    # Build PowerShell command
    ps_cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File'] + args
    try:
        proc = subprocess.run(ps_cmd, capture_output=True, text=True, check=False)
        return {"ok": proc.returncode == 0, "rc": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == '__main__':
    # CLI convenience for developers
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--clear-cache', action='store_true')
    p.add_argument('--harvest-count', type=int, default=1)
    p.add_argument('--start-server', action='store_true')
    args = p.parse_args()
    r = run_launch_live(dry_run=args.dry_run, clear_cache=args.clear_cache, harvest_count=args.harvest_count, start_server=args.start_server)
    print(r)
