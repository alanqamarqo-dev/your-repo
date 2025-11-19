# -*- coding: utf-8 -*-
import os, subprocess, sys, unittest

class TestInterpretiveReport(unittest.TestCase):
    def test_builds_html(self):
        out = os.path.join("reports","interpretive_report.html")
        if os.path.exists(out):
            os.remove(out)
        cmd = [
            sys.executable, "-m", "scripts.report_phaseI",
            "--models-dir", "artifacts/models",
            "--gen-dir", "artifacts/generalization",
            "--out", out
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertTrue(os.path.exists(out), "HTML report not written")

if __name__ == "__main__":
    unittest.main()
