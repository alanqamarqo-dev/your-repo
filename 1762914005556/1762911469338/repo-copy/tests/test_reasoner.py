import unittest
from pathlib import Path
import json

from Learning_System.Reasoner import Reasoner
import tempfile
import shutil

class ReasonerSmokeTest(unittest.TestCase):
    def setUp(self):
        # Create a minimal KB used by tests in an isolated temp dir
        self.tmpdir = tempfile.mkdtemp(prefix="test_reasoner_")
        self.kb_dir = Path(self.tmpdir)
        self.kb_path = self.kb_dir / "Learned_Patterns.json"
        sample = {
            "patterns": [
                {"base": "ohm", "winner": "linear", "fit": {"a": 2.0, "b": 0.1}, "schema": "V = a*I + b"},
                {"base": "exp1", "winner": "exp1", "fit": {"a": -0.5, "b": 1.0}, "schema": "y = b + exp(a*x)"},
                {"base": "projectile", "winner": "poly2", "fit": {"a": -4.9, "b": 0.0, "c": 1.0}, "schema": "y = a*x^2 + b*x + c"},
                {"base": "poly2", "winner": "poly2", "fit": {"a": 0.5, "b": 1.0, "c": 0.0}, "schema": "V = a*I^2 + b*I + c"},
                {"base": "hooke", "winner": "linear", "fit": {"a": 3.3, "b": 0.0}, "schema": "F = a*x + b"}
            ]
        }
        with self.kb_path.open("w", encoding="utf-8") as f:
            json.dump(sample, f, ensure_ascii=False, indent=2)

    def tearDown(self):
        try:
            shutil.rmtree(self.tmpdir)
        except Exception:
            pass

    def test_tau_from_exp(self):
        r = Reasoner(kb_path=self.kb_path)
        ans = r.query("what is tau for rc step?")
        self.assertTrue(ans.ok)
        self.assertIn("tau", ans.result)
        self.assertAlmostEqual(ans.result["tau"], 2.0)  # since a = -0.5 -> tau = -1/a = 2

    def test_g_from_projectile(self):
        r = Reasoner(kb_path=self.kb_path)
        ans = r.query("estimate g from projectile")
        self.assertTrue(ans.ok)
        self.assertIn("g_approx", ans.result)
        self.assertAlmostEqual(ans.result["g_approx"], -9.8)

    def test_R_from_ohm(self):
        r = Reasoner(kb_path=self.kb_path)
        ans = r.query("what is R?")
        self.assertTrue(ans.ok)
        self.assertIn("R", ans.result)
        self.assertAlmostEqual(ans.result["R"], 2.0)

    def test_k_from_hooke(self):
        r = Reasoner(kb_path=self.kb_path)
        ans = r.query("spring constant k=")
        self.assertTrue(ans.ok)
        self.assertIn("k", ans.result)
        self.assertAlmostEqual(ans.result["k"], 3.3)

    def test_dVdI_poly2(self):
        r = Reasoner(kb_path=self.kb_path)
        ans = r.query("compute dV/dI at I=2")
        self.assertTrue(ans.ok)
        self.assertIn("dVdI", ans.result)
        # a = 0.5 -> dV/dI = 2*a*I = 2*0.5*2 = 2.0
        self.assertAlmostEqual(ans.result["dVdI"], 2.0)

if __name__ == '__main__':
    unittest.main()
