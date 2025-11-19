"""
Lightweight safety/governance helpers for AGL.
Implements environment-driven defaults and helper functions:
- autonomy budget and controls
- network/disk/exec permission checks
- simple human-in-the-loop approval queue via artifacts/approvals
- kill-switch via artifacts/controls/STOP
- decision & risk logging

This module is intentionally minimal and non-invasive. Callers should
use these helpers to gate sensitive actions.
"""
from __future__ import annotations
import os
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any

ROOT = Path('.')
ARTIFACTS = ROOT / 'artifacts'
CONTROLS_DIR = ARTIFACTS / 'controls'
APPROVALS_DIR = ARTIFACTS / 'approvals'
LOGS_DIR = ARTIFACTS / 'logs'

# Ensure directories exist when module imported (safe, idempotent)
for d in (CONTROLS_DIR, APPROVALS_DIR, LOGS_DIR):
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

# Env-driven defaults (as suggested)
AGL_AUTONOMY_ENABLED = os.environ.get('AGL_AUTONOMY_ENABLED', '1') == '1'
AGL_AUTONOMY_BUDGET_SECONDS = int(os.environ.get('AGL_AUTONOMY_BUDGET_SECONDS', '1800'))
AGL_AUTONOMY_BUDGET_CALLS = int(os.environ.get('AGL_AUTONOMY_BUDGET_CALLS', '200'))
AGL_GOAL_PARALLELISM = int(os.environ.get('AGL_GOAL_PARALLELISM', '1'))

AGL_ALLOW_NETWORK = os.environ.get('AGL_ALLOW_NETWORK', '0') == '1'
AGL_ALLOW_DISK_WRITE = os.environ.get('AGL_ALLOW_DISK_WRITE', 'artifacts/,logs/')
AGL_ALLOW_EXEC_SHELL = os.environ.get('AGL_ALLOW_EXEC_SHELL', '0') == '1'
AGL_SECRETS_PATH = os.environ.get('AGL_SECRETS_PATH', '')

AGL_REQUIRE_APPROVAL_FOR = None
try:
    # support JSON-ish env var like '{"network":true}' if set
    raw = os.environ.get('AGL_REQUIRE_APPROVAL_FOR')
    if raw:
        AGL_REQUIRE_APPROVAL_FOR = json.loads(raw)
    else:
        AGL_REQUIRE_APPROVAL_FOR = {"network": True, "exec": True, "external_write": True}
except Exception:
    AGL_REQUIRE_APPROVAL_FOR = {"network": True, "exec": True, "external_write": True}

AGL_DECISION_NOTES = os.environ.get('AGL_DECISION_NOTES', '1') == '1'
AGL_RISK_LOG = os.environ.get('AGL_RISK_LOG', '1') == '1'
AGL_SNAPSHOT_ASYNC = os.environ.get('AGL_SNAPSHOT_ASYNC', '1') == '1'

AGL_GLOBAL_TIMEOUT_SECONDS = int(os.environ.get('AGL_GLOBAL_TIMEOUT_SECONDS', '3600'))

# Internal usage counters for the autonomy budget
_autonomy_start_time = time.time()
_autonomy_call_count = 0

# Helpers

def _log(msg: str):
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        p = LOGS_DIR / 'safety.log'
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        with p.open('a', encoding='utf-8') as fh:
            fh.write(f"[{t}] {msg}\n")
    except Exception:
        # best-effort logging only
        pass


def is_autonomy_enabled() -> bool:
    return bool(AGL_AUTONOMY_ENABLED)


def check_autonomy_budget_allowance() -> bool:
    """Return True if autonomy budget remains; also increments call counter."""
    global _autonomy_call_count
    _autonomy_call_count += 1
    elapsed = time.time() - _autonomy_start_time
    if elapsed > AGL_AUTONOMY_BUDGET_SECONDS:
        _log(f"Autonomy budget exhausted by time: elapsed={elapsed}")
        return False
    if _autonomy_call_count > AGL_AUTONOMY_BUDGET_CALLS:
        _log(f"Autonomy budget exhausted by calls: calls={_autonomy_call_count}")
        return False
    return True


def check_kill_switch() -> bool:
    """Return True if kill-switch is active (i.e., STOP file exists)."""
    stop_file = CONTROLS_DIR / 'STOP'
    if stop_file.exists():
        _log('Kill-switch detected; stopping operations')
        return True
    return False


def allow_network() -> bool:
    if check_kill_switch():
        return False
    if not AGL_ALLOW_NETWORK:
        if AGL_REQUIRE_APPROVAL_FOR.get('network', True):
            _log('Network access blocked by policy (requires approval)')
        return False
    return True


def allow_exec_shell() -> bool:
    if check_kill_switch():
        return False
    if not AGL_ALLOW_EXEC_SHELL:
        if AGL_REQUIRE_APPROVAL_FOR.get('exec', True):
            _log('Shell execution blocked by policy (requires approval)')
        return False
    return True


def _is_path_allowed_write(path: str) -> bool:
    # permit writing only under paths listed in AGL_ALLOW_DISK_WRITE (comma-separated)
    allowed = [p.strip() for p in AGL_ALLOW_DISK_WRITE.split(',') if p.strip()]
    p = Path(path).resolve()
    for a in allowed:
        try:
            a_path = Path(a).resolve()
            if a_path == p or a_path in p.parents:
                return True
        except Exception:
            continue
    return False


def allow_disk_write(path: str) -> bool:
    if check_kill_switch():
        return False
    if _is_path_allowed_write(path):
        return True
    # if not allowed, log and require approval if configured
    if AGL_REQUIRE_APPROVAL_FOR.get('external_write', True):
        _log(f'Attempted write to disallowed path: {path}')
    return False


def request_approval(action: str, details: Optional[Dict[str, Any]] = None) -> Path:
    """Create a pending approval JSON file under artifacts/approvals and return its path.
    Human operator can edit the file to add "approved": true.
    """
    APPROVALS_DIR.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    fid = f"approval_{action}_{now}.json"
    p = APPROVALS_DIR / fid
    payload = {'action': action, 'details': details or {}, 'approved': False, 'requested_at': now}
    try:
        with p.open('w', encoding='utf-8') as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        _log(f'Requested approval: {p} (action={action})')
    except Exception:
        _log(f'Failed to write approval request: {p}')
    return p


def check_approval(action: str, recent_seconds: int = 3600) -> bool:
    """Check approvals directory for any approved file matching the action within recent_seconds."""
    now = int(time.time())
    for f in APPROVALS_DIR.glob('approval_*.json'):
        try:
            j = json.load(f.open('r', encoding='utf-8'))
            if j.get('action') == action and j.get('approved'):
                # optionally check timing
                if now - int(j.get('requested_at', 0)) < recent_seconds:
                    _log(f'Found approval for action {action} in {f}')
                    return True
        except Exception:
            continue
    return False


def require_approval(action: str, details: Optional[Dict[str, Any]] = None) -> bool:
    """If an approval is required by policy, request and wait for simple approval.
    This function is intentionally non-blocking: it returns False if not yet approved.
    Callers should implement their own polling/notification flow or human intervention.
    """
    if not AGL_REQUIRE_APPROVAL_FOR.get(action, True):
        return True
    # check existing approvals first
    if check_approval(action):
        return True
    # create a request and return False to indicate manual step required
    request_approval(action, details)
    _log(f'Approval required for {action}; requested approval file')
    return False


def record_decision(note: str, meta: Optional[Dict[str, Any]] = None):
    if not AGL_DECISION_NOTES:
        return
    data = {'note': note, 'meta': meta or {}, 'ts': int(time.time())}
    p = LOGS_DIR / 'decision_notes.jsonl'
    try:
        with p.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(data, ensure_ascii=False) + '\n')
    except Exception:
        pass


def record_risk(entry: str, meta: Optional[Dict[str, Any]] = None):
    if not AGL_RISK_LOG:
        return
    data = {'risk': entry, 'meta': meta or {}, 'ts': int(time.time())}
    p = LOGS_DIR / 'risk_log.jsonl'
    try:
        with p.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(data, ensure_ascii=False) + '\n')
    except Exception:
        pass

# Convenience decorator for gating functions that perform sensitive actions
from functools import wraps

def gated(action: str):
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if check_kill_switch():
                raise RuntimeError('Operation aborted: kill-switch active')
            if not is_autonomy_enabled():
                raise RuntimeError('Autonomy disabled by config')
            if not check_autonomy_budget_allowance():
                raise RuntimeError('Autonomy budget exhausted')
            # require approval if configured
            if AGL_REQUIRE_APPROVAL_FOR.get(action, True) and not check_approval(action):
                # create a request and abort the action for safety
                request_approval(action, {'func': getattr(func, '__name__', None)})
                raise PermissionError(f'Approval required for action: {action}. Approval requested.')
            return func(*args, **kwargs)
        return wrapper
    return deco

# Simple runtime check helper for tripwires

def tripwire_check(conf_std: float, low_conf_frac: float, conf_std_thresh: float = 1.0, low_conf_frac_thresh: float = 0.5) -> bool:
    """Return True if tripwire triggered (values above thresholds)."""
    if conf_std > conf_std_thresh or low_conf_frac > low_conf_frac_thresh:
        record_risk('Tripwire triggered', {'conf_std': conf_std, 'low_conf_frac': low_conf_frac})
        return True
    return False

# Module ready
__all__ = [
    'is_autonomy_enabled', 'check_autonomy_budget_allowance', 'check_kill_switch',
    'allow_network', 'allow_disk_write', 'allow_exec_shell', 'require_approval',
    'request_approval', 'check_approval', 'record_decision', 'record_risk', 'gated',
    'tripwire_check'
]
