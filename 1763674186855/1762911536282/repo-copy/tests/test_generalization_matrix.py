# -*- coding: utf-8 -*-
import os
import json
import tempfile
import shutil
import unittest

from Learning_System.GeneralizationMatrix import run_generalization

SAMPLE_KB = {
    "version": "G.1",
    "updated_at": "2025-10-17T00:00:00Z",
    "patterns": [
        {"base": "ohm", "winner": "ohm", "fit": {"a": 10.0, "b": 0.0, "rmse": 0.0, "n": 6}},
        {"base": "rc_step", "winner": "exp1", "fit": {"a": -0.02, "b": 5.0, "rmse": 0.01, "n": 11}},
        {"base": "projectile", "winner": "poly2", "fit": {"a": 4.9, "b": 0.0, "rmse": 0.01, "n": 11}},
        {"base": "poly2", "winner": "poly2", "fit": {"a": 11.0, "b": -0.1, "rmse": 0.08, "n": 11}},
    ]
}


class TestGeneralizationMatrix(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="agl_gen_")
        self.kb = os.path.join(self.tmp, "Learned_Patterns.json")
        with open(self.kb, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_KB, f, ensure_ascii=False, indent=2)
        self.out = os.path.join(self.tmp, "artifacts", "generalization")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_bundle_and_relations(self):
        bundle = run_generalization(self.kb, self.out)
        self.assertGreater(bundle["count"], 0)
        bundle_path = os.path.join(self.out, "generalization_bundle.json")
        self.assertTrue(os.path.exists(bundle_path))

        # تحقّق من العلاقات الأساسية
        from Learning_System.io_utils import read_text
        txt = read_text(bundle_path)
        self.assertIn("ohm->power", txt)
        self.assertIn("rc_exp->tau", txt)
        self.assertIn("projectile->g", txt)
        self.assertIn("poly2->differential_slope", txt)

        # ملفات تفصيلية
        self.assertTrue(os.path.exists(os.path.join(self.out, "ohm_power.json".replace("->", "_"))))
        self.assertTrue(os.path.exists(os.path.join(self.out, "rc_exp_tau.json".replace("->", "_"))))
        self.assertTrue(os.path.exists(os.path.join(self.out, "projectile_g.json")))
        self.assertTrue(os.path.exists(os.path.join(self.out, "poly2_differential_slope.json")))


if __name__ == "__main__":
    unittest.main()
