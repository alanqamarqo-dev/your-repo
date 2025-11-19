import os
import sys
import json
import subprocess
import pathlib


def test_full_integration_runs_all_together(tmp_path):
    """Integration test: run the orchestrator which will run the engines compiler.

    By default this test runs in mock mode (no network). To run live set
    the env var `AGL_INTEGRATION_LIVE=1` and ensure `OPENAI_API_KEY` is present
    in the session. The test asserts that the orchestrator completes and
    produces an `engines_report` in the JSON output.
    """

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    orch_script = repo_root / 'scripts' / 'orchestrate.py'
    assert orch_script.exists(), f"orchestrate script not found at {orch_script}"

    live = os.environ.get('AGL_INTEGRATION_LIVE', '0') == '1'

    env = os.environ.copy()
    # default to mock mode to avoid network unless explicitly requested
    if not live:
        env['AGL_EXTERNAL_INFO_MOCK'] = '1'

    cmd = [sys.executable, str(orch_script), '--task', 'derive', '--base', '2', '--run-engines']
    if live:
        cmd.append('--engines-live')

    proc = subprocess.run(cmd, cwd=str(repo_root), env=env, capture_output=True, text=True, timeout=120)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()

    assert proc.returncode == 0, f"orchestrator failed (rc={proc.returncode}) stderr:\n{stderr}\nstdout:\n{stdout}"

    # Parse output JSON (should include orchestrator result and engines_report)
    # The orchestrator may print informational lines before the JSON; find the first '{'
    idx = stdout.find('{')
    assert idx != -1, f"No JSON object found in orchestrator stdout:\n{stdout}\nstderr:\n{stderr}"
    data = json.loads(stdout[idx:])
    assert 'orchestrator' in data
    # engines_report may be present when --run-engines used
    assert 'engines_report' in data, "engines_report missing from orchestrator output"

    # basic sanity checks on the engines_report
    er = data['engines_report']
    assert isinstance(er.get('engines', {}), dict)
    # ensure General_Knowledge included
    assert 'General_Knowledge' in er['engines']
