import unittest
import subprocess
import sys
import os
import json
import hashlib
import time


class TestAGLIntegrationCLI(unittest.TestCase):
    def setUp(self):
        # ensure reports folder exists and remove any previous report
        self.reports_path = os.path.join(os.getcwd(), 'reports')
        os.makedirs(self.reports_path, exist_ok=True)
        self.report_file = os.path.join(self.reports_path, 'last_run.json')
        try:
            if os.path.exists(self.report_file):
                os.remove(self.report_file)
        except Exception:
            pass

    def _run_agl_cli(self, task_text="اختبار التكامل"):
        # run AGL.py via the same python executable running the tests
        cmd = [sys.executable, os.path.join(os.getcwd(), 'AGL.py'), '--task', task_text, '--report', self.report_file]
        proc = subprocess.run(cmd, capture_output=True, timeout=20)
        return proc

    def _load_report(self):
        # allow a brief wait for file writing
        for _ in range(5):
            if os.path.exists(self.report_file):
                break
            time.sleep(0.2)
        with open(self.report_file, 'r', encoding='utf-8-sig') as f:
            return json.load(f)

    def _find_artifact_info(self, obj):
        # recursively search for artifact indicators
        if isinstance(obj, dict):
            # common keys
            for k, v in obj.items():
                if k in ('artifact_meta', 'artifact') and isinstance(v, dict):
                    return v
                if k in ('artifact_path', 'code_artifact', 'artifact_sha256') and v:
                    return {k: v}
                res = self._find_artifact_info(v)
                if res:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = self._find_artifact_info(item)
                if res:
                    return res
        return None

    def test_cli_writes_report(self):
        proc = self._run_agl_cli()
        self.assertEqual(proc.returncode, 0, msg=f"AGL CLI failed: {proc.stderr.decode('utf-8', errors='replace')}")
        self.assertTrue(os.path.exists(self.report_file), msg='reports/last_run.json not created')

    def test_report_has_core_fields(self):
        proc = self._run_agl_cli()
        self.assertEqual(proc.returncode, 0)
        report = self._load_report()
        # basic checks
        self.assertIn('solution', report)
        self.assertIn('signals', report)
        self.assertIn('confidence_score', report)
        self.assertIn('safety', report)
        # solution should be a dict with either a 'result' or a confidence field
        sol = report.get('solution')
        self.assertIsInstance(sol, dict)
        self.assertTrue('result' in sol or 'confidence' in sol)

    def test_artifact_file_if_present(self):
        proc = self._run_agl_cli()
        self.assertEqual(proc.returncode, 0)
        report = self._load_report()
        # search for artifact info
        art = self._find_artifact_info(report)
        if not art:
            self.skipTest('No artifact information found in report')

        # If art is a mapping with path or meta, adapt
        path = None
        expected_sha = None
        if 'artifact_path' in art:
            path = art.get('artifact_path')
        elif 'code_artifact' in art:
            path = art.get('code_artifact')
        elif 'artifact' in art and isinstance(art.get('artifact'), str):
            path = art.get('artifact')
        elif art.get('path'):
            path = art.get('path')
        elif art.get('exists') is not None and art.get('exists') is False:
            self.fail('artifact_meta exists==False in report')

        # artifact_meta might contain sha256
        if art.get('sha256'):
            expected_sha = art.get('sha256')
        if art.get('artifact_sha256'):
            expected_sha = art.get('artifact_sha256')

        if not path:
            # maybe artifact_meta had no path but had exists/size/sha256; look for any file mentioned elsewhere
            self.skipTest('Artifact reported but no path could be discovered')

        self.assertTrue(os.path.exists(path), msg=f'Artifact path listed but file missing: {path}')
        size = os.path.getsize(path)
        self.assertGreater(size, 0, msg='Artifact file size is zero')

        if expected_sha:
            h = hashlib.sha256()
            with open(path, 'rb') as f:
                h.update(f.read())
            self.assertEqual(h.hexdigest(), expected_sha, msg='Artifact SHA256 does not match report')


if __name__ == '__main__':
    unittest.main()
