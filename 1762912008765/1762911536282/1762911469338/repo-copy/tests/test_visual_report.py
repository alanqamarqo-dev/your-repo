import os, sys, subprocess, json, glob
import unittest

class TestVisualReport(unittest.TestCase):
    def test_make_visual_report(self):
        out = subprocess.run(
            [sys.executable, "-m", "scripts.make_visual_report",
             "--glob-dir", "artifacts/models",
             "--out", "reports/models_visual.html",
             "--figdir", "reports/figs"],
            capture_output=True, text=True
        )
        self.assertEqual(out.returncode, 0, msg=out.stderr)
        self.assertTrue(os.path.exists("reports/models_visual.html"))
        # تأكد من توليد صور على الأقل لملف واحد
        pngs = glob.glob("reports/figs/*.png")
        self.assertTrue(len(pngs) >= 1)

if __name__ == "__main__":
    unittest.main()
