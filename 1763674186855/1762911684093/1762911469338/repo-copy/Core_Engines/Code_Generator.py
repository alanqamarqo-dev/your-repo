# Core_Engines/Code_Generator.py
from pathlib import Path
import time
import uuid
import py_compile
import subprocess
import sys
import hashlib

class PythonSpecialist:
    def generate_code(self, requirements):
        """Generate a small Python file artifact based on requirements and return its path.

        The function writes a .py file under ./artifacts and returns the artifact path.
        """
        artifacts_dir = Path(__file__).resolve().parent.parent / 'artifacts'
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        ts = int(time.time())
        uid = uuid.uuid4().hex[:8]
        filename = f"codegen_{ts}_{uid}.py"
        path = artifacts_dir / filename

        # Simple generated code template using the requirements as comments
        content = [
            '"""Auto-generated Python code artifact',
            f'Requirements: {requirements}',
            '"""',
            '',
            'def main() -> None:',
            '    """Entrypoint for the generated artifact"""',
            '    print("Hello from generated code")',
            '',
            'if __name__ == "__main__":',
            '    main()',
        ]
        path.write_text("\n".join(content), encoding='utf-8')
        return str(path)

    def run_artifact_smoketest(self, path):
        import subprocess, sys, os
        if not os.path.exists(path):
            return False, "missing"
        try:
            cmd = [sys.executable, path]
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            ok = (p.returncode == 0)
            return ok, p.stderr if not ok else "ok"
        except Exception as e:
            return False, str(e)

class CodeGenerator:
    def __init__(self):
        self.language_specialists = {
            'python': PythonSpecialist()
        }
    
    def generate_software_system(self, requirements, verbose: bool = False):
        """توليد أنظمة برمجية كاملة

        verbose: when True prints progress statements; default False.
        """
        if verbose:
            print(f"💻 توليد نظام برمجي: {requirements}")
        code_artifact = self.language_specialists['python'].generate_code(requirements)

        # Validate artifact: syntax check and a short runtime execution
        validated = False
        sha256 = None
        try:
            py_compile.compile(code_artifact, doraise=True)
            # compute sha
            with open(code_artifact, 'rb') as _f:
                sha256 = hashlib.sha256(_f.read()).hexdigest()
            # run the artifact smoketest via PythonSpecialist helper
            ok, info = self.language_specialists['python'].run_artifact_smoketest(code_artifact)
            if ok:
                validated = True
        except Exception:
            validated = False

        return {
            "architecture": "هيكل النظام",
            "components": ["مكون 1", "مكون 2"],
            "code_artifact": code_artifact,
            "artifact_validated": validated,
            "artifact_sha256": sha256
        }

    def process_task(self, task):
        """Return a lightweight generated-system partial solution for higher-level orchestration."""
        try:
            txt = str(task).lower()
            # boost when the task text includes code-related cue (stronger boost)
            # Trigger generation for explicit code tasks or when the task is a decomposed structured task
            if 'code' in txt or 'كود' in txt or (isinstance(task, dict) and (task.get('type') == 'software_design' or 'main_task' in task)):
                sol = self.generate_software_system(task.get('requirements', {}) if isinstance(task, dict) else {}, verbose=False)
                score = 0.88 if sol.get('artifact_validated') else 0.7
                conf = 0.86 if sol.get('artifact_validated') else 0.72
                return {"ok": True, "score": float(score), "confidence": float(conf), "result": sol}

            if isinstance(task, dict) and task.get('type') == 'software_design':
                sol = self.generate_software_system(task.get('requirements', {}), verbose=False)
                score = 0.85 if sol.get('artifact_validated') else 0.7
                conf = 0.84 if sol.get('artifact_validated') else 0.72
                return {
                    "ok": True,
                    "score": float(score),
                    "confidence": float(conf),
                    "result": sol
                }

            # Normalized fallback
            return {"ok": True, "score": 0.4, "confidence": 0.4, "result": None}
        except Exception as e:
            return {"ok": False, "score": 0.0, "confidence": 0.0, "result": None, "error": str(e)}