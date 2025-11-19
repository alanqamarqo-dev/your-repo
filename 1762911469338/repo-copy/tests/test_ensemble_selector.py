import os, json, tempfile, shutil, unittest
from Learning_System.Ensemble_Selector import (
    CandidateFit, EnsembleSelector, run_ensemble_over_folder
)

class TestEnsembleSelector(unittest.TestCase):
    def test_pick_lowest_rmse(self):
        fits = [
            CandidateFit("exp1", rmse=0.2, confidence=0.6, params={"a":1.0,"b":2.0}, n=10),
            CandidateFit("poly2", rmse=0.1, confidence=0.4, params={"a":0.1,"b":9.9}, n=10),
        ]
        sel = EnsembleSelector().select(fits)
        self.assertTrue(sel["success"])
        self.assertEqual(sel["result"]["winner"], "poly2")
        self.assertAlmostEqual(sel["result"]["rmse"], 0.1, places=6)

    def test_blend_when_close_and_same_family(self):
        # rmse متقارب ضمن 5% ونفس العائلة => مزج
        fits = [
            CandidateFit("poly2", rmse=0.100, confidence=0.6, params={"a":0.1,"b":10.0}, n=11),
            CandidateFit("poly2", rmse=0.102, confidence=0.9, params={"a":0.11,"b":9.9}, n=11),
        ]
        sel = EnsembleSelector().select(fits)
        self.assertTrue(sel["success"])
        self.assertTrue(sel["result"]["blended"])
        self.assertIn("a", sel["result"]["params"])
        self.assertIn("b", sel["result"]["params"])
        self.assertLessEqual(sel["result"]["rmse"], 0.102)

    def test_tooling_over_folder(self):
        tmp = tempfile.mkdtemp()
        try:
            models = os.path.join(tmp, "artifacts", "models")
            os.makedirs(models, exist_ok=True)
            src = os.path.join(models, "poly2_D", "results.json")
            os.makedirs(os.path.dirname(src), exist_ok=True)
            sample = {
                "base": "poly2_iv",
                "yname": "V", "xname": "I",
                "results":[
                    {"candidate":"poly2","fit":{"a":0.1,"b":10.0,"rmse":1e-4,"n":11,"confidence":0.9}},
                    {"candidate":"poly2","fit":{"a":0.11,"b":9.9,"rmse":1.02e-4,"n":11,"confidence":0.95}}
                ]
            }
            with open(src,"w",encoding="utf-8") as f: json.dump(sample,f,ensure_ascii=False,indent=2)

            from Learning_System import Ensemble_Selector
            # شغّل على المجلد المؤقت
            processed = Ensemble_Selector.run_ensemble_over_folder(
                src_dir=os.path.join(tmp,"artifacts","models"),
                src_suffix="_D/results.json",
                dst_suffix="_E/results.json"
            )
            self.assertEqual(len(processed), 1)
            dst = processed[0][1]
            self.assertTrue(os.path.exists(dst))
            with open(dst, "r", encoding="utf-8") as f:
                out = json.load(f)
            self.assertTrue(out["ensemble"]["success"])
            self.assertTrue(out["ensemble"]["result"]["blended"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
