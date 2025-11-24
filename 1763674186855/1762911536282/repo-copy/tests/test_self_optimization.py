# tests/test_self_optimization.py
import subprocess, sys, os, json, tempfile, shutil, pathlib, unittest

class TestSelfOptimizationSmoke(unittest.TestCase):
    def test_cli_runs_and_writes_outputs(self):
        outdir = os.path.join("reports","self_optimization")
        if os.path.exists(outdir):
            shutil.rmtree(outdir, ignore_errors=True)
        cmd = [sys.executable, "-m", "scripts.self_optimize", "--out", outdir]
        out = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, msg=out.stderr)
        self.assertTrue(os.path.exists(os.path.join(outdir,"self_optimization.json")))
        from Learning_System.io_utils import read_json
        j = read_json(os.path.join(outdir, "self_optimization.json"))
        self.assertEqual(j.get("status"), "ok")
        self.assertIn("fusion_weights", j)
