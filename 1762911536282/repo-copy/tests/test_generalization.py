# tests/test_generalization.py
import os, json, tempfile
import unittest
from Learning_System.Generalizer import Generalizer

class TestGeneralization(unittest.TestCase):
    def setUp(self):
        self.gen = Generalizer()

    def _save(self, obj) -> str:
        d = tempfile.mkdtemp()
        p = os.path.join(d, "results.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        return p

    def test_hooke_to_energy(self):
        # فائز Hooke بمعامل k≈100
        res = {
            "base": "hooke",
            "ensemble": {"result": {"winner": "hooke", "params": {"a": 100.0}}},
        }
        p = self._save(res)
        out = self.gen.derive(p, x=0.2)   # x_sample
        self.assertEqual(out["relation"], "hooke->energy")
        self.assertAlmostEqual(out["derived"]["E"], 0.5*100*(0.2**2), places=9)

    def test_ohm_to_power(self):
        res = {"base": "ohm", "ensemble": {"result": {"winner": "ohm", "params": {"a": 10.0}}}}
        p = self._save(res)
        out = self.gen.derive(p, I=2.0)
        self.assertEqual(out["relation"], "ohm->power")
        self.assertAlmostEqual(out["derived"]["P_I2R"], (2.0**2)*10.0, places=9)

if __name__ == "__main__":
    unittest.main()
