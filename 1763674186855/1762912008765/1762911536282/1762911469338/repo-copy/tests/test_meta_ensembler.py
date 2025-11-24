import unittest
import numpy as np
from Core_Engines.Meta_Ensembler import MetaEnsembler, CandidateSignal

class TestMetaEnsembler(unittest.TestCase):
    def test_sigma_weighting(self):
        np.random.seed(0)
        n = 50
        x = np.linspace(0,1,n)
        y_true = 2*x + 1
        # نموذج A قريب لكن سيغما صغيرة (يجب وزنه أعلى)
        y_a = y_true + np.random.normal(0, 0.05, n)
        sig_a = np.full(n, 0.05)
        # نموذج B أضعف بسيغما أكبر
        y_b = y_true + np.random.normal(0, 0.20, n)
        sig_b = np.full(n, 0.20)

        ens = MetaEnsembler()
        out = ens.blend([
            CandidateSignal("A", y_a, sigma=sig_a),
            CandidateSignal("B", y_b, sigma=sig_b),
        ])
        y = out["y"]
        rmse_a = np.sqrt(np.mean((y_a - y_true)**2))
        rmse_b = np.sqrt(np.mean((y_b - y_true)**2))
        rmse_y = np.sqrt(np.mean((y - y_true)**2))
        self.assertLess(rmse_y, rmse_b)
        # عادةً سيكون rmse_y <= rmse_a (أو قريب جدًا)
        # allow tiny numerical tolerance
        self.assertLessEqual(rmse_y, rmse_a + 1e-3)

    def test_confidence_weighting(self):
        n = 30
        y_true = np.zeros(n)
        y_a = np.zeros(n) + 0.1
        y_b = np.zeros(n) + 1.0
        ens = MetaEnsembler()
        out = ens.blend([
            CandidateSignal("A", y_a, confidence=0.9),
            CandidateSignal("B", y_b, confidence=0.1),
        ])
        y = out["y"]
        self.assertTrue(np.all(y < 0.6))  # أقرب إلى A
        self.assertEqual(y.shape, (n,))

    def test_fallback_mean(self):
        n = 10
        y_a = np.ones(n) * 1.0
        y_b = np.ones(n) * 3.0
        ens = MetaEnsembler()
        out = ens.blend([
            CandidateSignal("A", y_a),
            CandidateSignal("B", y_b),
        ])
        y = out["y"]
        self.assertTrue(np.allclose(y, 2.0))

if __name__ == "__main__":
    unittest.main()
