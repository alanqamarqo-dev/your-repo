"""Safe self-modification scaffolding (dry-run first, pluggable validators and sandbox).
This is a minimal, safe implementation following the architecture you provided.

Enhancements in this file:
- Optional sandbox directory where a limited "live apply" can be exercised for tests.
- `allow_live_apply` flag to enable writing changes into the sandbox only (never modify real system).
"""
import time
import os
import json
from typing import Any, Dict, Optional


class SandboxEnvironment:
    def __init__(self, sandbox_dir: Optional[str] = None):
        self.sandbox_dir = sandbox_dir
        if self.sandbox_dir:
            os.makedirs(self.sandbox_dir, exist_ok=True)

    def _apply_steps_to_sandbox(self, steps):
        results = []
        for step in steps:
            op = step.get('op')
            if op == 'write_file':
                # path is relative to sandbox
                path = step.get('path')
                content = step.get('content', '')
                if not path:
                    results.append({'ok': False, 'op': op, 'reason': 'missing path'})
                    continue
                dest = os.path.join(self.sandbox_dir, path)
                os.makedirs(os.path.dirname(dest) or self.sandbox_dir, exist_ok=True)
                with open(dest, 'w', encoding='utf-8') as f:
                    f.write(content)
                results.append({'ok': True, 'op': op, 'path': dest})
            elif op == 'append_memory':
                # simple memory append stored as json list per key
                key = step.get('key', 'default')
                value = step.get('value')
                mem_file = os.path.join(self.sandbox_dir, f'memory_{key}.json')
                try:
                    if os.path.exists(mem_file):
                        with open(mem_file, 'r', encoding='utf-8') as f:
                            arr = json.load(f)
                    else:
                        arr = []
                    arr.append(value)
                    with open(mem_file, 'w', encoding='utf-8') as f:
                        json.dump(arr, f, indent=2)
                    results.append({'ok': True, 'op': op, 'file': mem_file})
                except Exception as e:
                    results.append({'ok': False, 'op': op, 'reason': str(e)})
            else:
                # unknown ops are treated as simulated
                results.append({'ok': True, 'op': op, 'details': 'simulated (no-op for unknown op)'})
        return results

    def execute(self, modification_plan: Dict[str, Any]) -> Dict[str, Any]:
        # If sandbox_dir is set, attempt to perform safe, limited operations there
        steps = modification_plan.get('steps', []) if isinstance(modification_plan, dict) else []
        if self.sandbox_dir and steps:
            results = self._apply_steps_to_sandbox(steps)
            ok = all((r.get('ok') for r in results))
            return {"ok": ok, "details": "sandbox execution", "results": results}

        # Dry-run execution: do not change live system; simulate results
        return {"ok": True, "details": "simulated execution", "plan": modification_plan}


class ModificationValidator:
    def __init__(self):
        pass

    def validate(self, modification_plan: Dict[str, Any]) -> bool:
        # Basic validation: ensure plan is a dict and contains steps
        if not isinstance(modification_plan, dict):
            return False
        if 'steps' not in modification_plan:
            return False
        return True


class RollbackManager:
    def __init__(self):
        self.snapshots = []

    def create_snapshot(self, state: Dict[str, Any], sandbox_dir: Optional[str] = None):
        snapshot = {'ts': time.time(), 'state': state}
        # If sandbox_dir provided, capture a lightweight listing of sandbox files
        if sandbox_dir:
            files = []
            for root, _dirs, filenames in os.walk(sandbox_dir):
                for fn in filenames:
                    rel = os.path.relpath(os.path.join(root, fn), sandbox_dir)
                    files.append(rel)
            snapshot['sandbox_files'] = files
        self.snapshots.append(snapshot)

    def restore_last(self):
        if not self.snapshots:
            return None
        return self.snapshots.pop()


class PerformanceMonitor:
    def __init__(self):
        self.baselines = {}

    def record_baseline(self, name: str, metrics: Dict[str, Any]):
        self.baselines[name] = metrics

    def check(self, metrics: Dict[str, Any]) -> bool:
        # Very small placeholder: always true (no regression)
        return True


class SafeSelfModificationSystem:
    def __init__(self, sandbox_dir: Optional[str] = None, allow_live_apply: bool = False):
        """Create a SafeSelfModificationSystem.

        sandbox_dir: optional path where limited live apply may be written for tests.
        allow_live_apply: if True, `apply_to_live_system` will write into sandbox_dir instead of real system.
        """
        self.sandbox_dir = sandbox_dir
        self.allow_live_apply = allow_live_apply
        self.sandbox_environment = SandboxEnvironment(sandbox_dir=self.sandbox_dir)
        self.modification_validator = ModificationValidator()
        self.rollback_manager = RollbackManager()
        self.performance_monitor = PerformanceMonitor()

    def verify_modification_success(self, sandbox_result: Dict[str, Any]) -> bool:
        # Very simple acceptance: sandbox must return ok=True
        return bool(sandbox_result.get('ok'))

    def apply_to_live_system(self, modification_plan: Dict[str, Any]) -> Dict[str, Any]:
        # By default we do not modify any live system. However, for tests we allow a
        # guarded apply into the provided sandbox directory when allow_live_apply=True.
        if self.allow_live_apply and self.sandbox_dir:
            steps = modification_plan.get('steps', []) if isinstance(modification_plan, dict) else []
            results = self.sandbox_environment._apply_steps_to_sandbox(steps)
            ok = all((r.get('ok') for r in results))
            return {"applied": ok, "note": "applied into sandbox", "results": results}

        return {"applied": False, "note": "live apply disabled in safe implementation"}

    def analyze_and_improve(self, modification_plan: Dict[str, Any], sandbox_result: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder: return diagnostic info
        return {"status": "failed_in_sandbox", "details": sandbox_result}

    def safe_self_modify(self, modification_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a modification plan safely (validate -> sandbox -> verify -> (apply or analyze))."""
        if not self.modification_validator.validate(modification_plan):
            return {"status": "rejected", "reason": "validation_failed"}
        # create snapshot (lightweight)
        self.rollback_manager.create_snapshot({'plan': modification_plan, 'ts': time.time()}, sandbox_dir=self.sandbox_dir)

        # execute in sandbox
        sandbox_result = self.sandbox_environment.execute(modification_plan)

        # verify
        if self.verify_modification_success(sandbox_result):
            live_result = self.apply_to_live_system(modification_plan)
            return {"status": "success", "result": live_result}
        else:
            return self.analyze_and_improve(modification_plan, sandbox_result)
