import json, os, unittest, subprocess, sys

PY = os.path.join(".venv", "Scripts", "python.exe")

class TestPhaseDUnified(unittest.TestCase):
    def run_train(self, data, x, y, out, candidates):
        cmd = [PY, "scripts/train_phaseD.py",
               "--data", data, "--x", x, "--y", y,
               "--candidates", *candidates, "--out", out]
        cp = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)

    def test_poly2_best(self):
        out = "artifacts/models/poly2_D_test"
        os.makedirs(out, exist_ok=True)
        self.run_train("data/phaseD/poly2_iv.csv", "I", "V", out,
                       ["poly2", "a*x**2", "k*x", "k*x + b"])
        with open(os.path.join(out, "results.json"), encoding="utf-8") as f:
            obj = json.load(f)
        best = min(obj["results"], key=lambda r: r["fit"]["rmse"])["candidate"]
        self.assertIn(best, ["poly2","a*x**2"])

    def test_exp1_present(self):
        out = "artifacts/models/rc_D_test"
        os.makedirs(out, exist_ok=True)
        self.run_train("data/phaseD/rc_step.csv", "t[s]", "Vc[V]", out,
                       ["exp1", "k*x", "k*x + b", "a*x**2"])
        with open(os.path.join(out, "results.json"), encoding="utf-8") as f:
            obj = json.load(f)
        names = [r["candidate"] for r in obj["results"]]
        self.assertIn("exp1", names)

if __name__ == "__main__":
    unittest.main()
