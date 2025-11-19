import unittest
from Learning_System.Law_Learner import fit_single_coeff_linear, fit_linear_with_intercept, fit_power_law


class TestLawModels(unittest.TestCase):
    def test_fit_single_coeff_linear_ok(self):
        data = {'y': [0.0, 3.5, 7.0], 'x': [0.0, 1.0, 2.0]}
        res = fit_single_coeff_linear('F=k*x', 'y', 'x', data)
        self.assertAlmostEqual(res['coef'], 3.5, places=6)
        self.assertEqual(res['n'], 3)

    def test_fit_linear_with_intercept(self):
        data = {'y': [1.0, 3.0, 5.0], 'x': [0.0, 1.0, 2.0]}
        res = fit_linear_with_intercept('y=a*x+b', 'y', 'x', data)
        self.assertAlmostEqual(res['a'], 2.0, places=6)

    def test_fit_power_law(self):
        data = {'y': [1.0, 4.0, 9.0], 'x': [1.0, 2.0, 3.0]}
        res = fit_power_law('y=a*x^n', 'y', 'x', data)
        # For y = x^2, expect n approx 2
        self.assertAlmostEqual(res['n'], 2.0, places=1)


if __name__ == '__main__':
    unittest.main()
