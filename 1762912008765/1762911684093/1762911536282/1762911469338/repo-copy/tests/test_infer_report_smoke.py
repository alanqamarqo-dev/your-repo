import os, glob, subprocess, sys, unittest

class TestInferReportSmoke(unittest.TestCase):
    def test_infer_report_smoke(self):
        out = subprocess.run([sys.executable, "scripts/infer_report.py", "--base", "ohm", "--x", "0.3"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, msg=out.stderr)
        files = sorted(glob.glob("reports/infer_ohm_*.html"))
        self.assertTrue(files, "no report generated")

if __name__ == '__main__':
    unittest.main()
