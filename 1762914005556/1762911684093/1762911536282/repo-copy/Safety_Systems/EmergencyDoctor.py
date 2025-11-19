import os
import sys
import time
import json
import subprocess
import logging
from typing import Dict, Any
from datetime import datetime, timezone
import textwrap


logging.basicConfig(level=logging.INFO)


class EmergencyDoctor:
    def __init__(self):
        self.active_containers: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger('EmergencyDoctor')

    def create_isolated_container(self, container_id: str, purpose: str = "emergency") -> Dict[str, Any]:
        """Create a minimal isolated workspace for an emergency task and register it."""
        base = os.path.abspath(os.path.join('reports', container_id))
        code_dir = os.path.join(base, 'code')
        data_dir = os.path.join(base, 'data')
        os.makedirs(code_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        now = datetime.now(timezone.utc)
        meta = {
            "id": container_id,
            "directory": base,
            "created_at": now.isoformat(),
            "purpose": purpose,
            "status": "ACTIVE"
        }
        self.active_containers[container_id] = meta
        return meta

    # backward-compatible alias
    register_container = create_isolated_container

    def _cleanup_container(self, container_id: str) -> bool:
        c = self.active_containers.get(container_id)
        if not c:
            return False
        # best-effort removal of directory; keep exceptions minimal
        try:
            # attempt to remove files we created, leave directory if OS prevents deletion
            code_dir = os.path.join(c['directory'], 'code')
            data_dir = os.path.join(c['directory'], 'data')
            if os.path.exists(code_dir):
                for fname in os.listdir(code_dir):
                    try:
                        os.remove(os.path.join(code_dir, fname))
                    except Exception:
                        pass
            if os.path.exists(data_dir):
                for fname in os.listdir(data_dir):
                    try:
                        os.remove(os.path.join(data_dir, fname))
                    except Exception:
                        pass
            # don't rmdir base to avoid surprising removal in CI; just mark inactive
            self.active_containers[container_id]['status'] = 'CLEANED'
            return True
        except Exception:
            return False

    def emergency_cleanup_all(self) -> None:
        for cid in list(self.active_containers.keys()):
            try:
                self._cleanup_container(cid)
            except Exception:
                pass

    def execute_in_emergency_container(self, container_id: str, code: str, task_data: Dict = None) -> Dict[str, Any]: # type: ignore
        container = self.active_containers.get(container_id)
        if not container:
            return {"success": False, "error": "container_not_found"}

        try:
            # ensure we use absolute paths to avoid cwd-relative duplication on Windows
            code_file = os.path.abspath(os.path.join(container["directory"], "code", "emergency_task.py"))
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(self._wrap_code_with_safety(code))

            return self._execute_safe_code(container_id, code_file, task_data or {})
        except Exception as e:
            self.logger.error(f"❌ failed to launch in container: {str(e)}")
            return {"success": False, "error": str(e)}

    def _wrap_code_with_safety(self, code: str) -> str:
        # Use a plain triple-quoted template and replace {CODE} with the code repr
        raw = """
# ⚠️ emergency isolated script wrapper
import sys, io, traceback, builtins

# minimal blocking of dangerous builtins
# NOTE: do not disable `exec` because this wrapper relies on calling exec()
# instead, disable eval and open. We avoid touching __import__ here because
# we override importlib.__import__ below.
for _name in ['eval', 'open']:
    try:
        setattr(builtins, _name, None)
    except Exception:
        pass

# block some modules by overriding import mechanism for safety (best-effort)
BLOCKED = {'os','sys','subprocess','socket','shutil','pathlib','ssl','ctypes'}
def _blocked_import(name, *args, **kwargs):
    if name.split('.')[0] in BLOCKED:
        raise ImportError("Blocked module: " + name)
    return __import__(name, *args, **kwargs)

import importlib
importlib.__import__ = _blocked_import

out = io.StringIO()
err = io.StringIO()
try:
    _globals = {}
    _locals = {}
    code = r{CODE}
    exec(code, _globals, _locals)
    print("EXECUTION_COMPLETED_SUCCESSFULLY")
except Exception as e:
    print("EMERGENCY_ERROR:" + str(e))
    traceback.print_exc()
"""
        code_repr = repr(code)
        return textwrap.dedent(raw).replace('{CODE}', code_repr)

    def _execute_safe_code(self, container_id: str, code_file: str, task_data: Dict) -> Dict[str, Any]:
        container = self.active_containers[container_id]
        workdir = os.path.join(container["directory"], "code")

        data_path = os.path.join(container["directory"], "data", "input.json")
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(task_data, f, ensure_ascii=False)

        env = os.environ.copy()
        env.pop("PYTHONPATH", None)

        cmd = [
            sys.executable,
            "-I",
            "-S",
            "-u",
            code_file,
        ]

        start = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=workdir,
                env=env,
                capture_output=True,
                text=True,
                timeout=30
            )
            elapsed = time.time() - start

            ok = (proc.returncode == 0) and ("EXECUTION_COMPLETED_SUCCESSFULLY" in proc.stdout)
            return {
                "success": ok,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "container_id": container_id,
                "execution_time": f"{elapsed:.2f}s",
                "resources_used": {"memory": "n/a", "cpu": "n/a"}
            }
        except subprocess.TimeoutExpired:
            self.logger.error("⏰ Timeout — killing execution")
            return {"success": False, "error": "timeout", "container_id": container_id}
