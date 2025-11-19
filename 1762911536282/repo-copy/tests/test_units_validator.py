import unittest
from Core_Engines.Units_Validator import check_dimensional_consistency


class TestUnitsValidator(unittest.TestCase):
    def setUp(self):
        self.dims = {
            "F": "kg*m/s^2",
            "m": "kg",
            "a": "m/s^2",
            "x": "m",
            "k": "kg/s^2",
        }

    def test_newton_ok(self):
        self.assertTrue(check_dimensional_consistency(["F"], ["m","*","a"], self.dims))

    def test_hooke_ok(self):
        self.assertTrue(check_dimensional_consistency(["F"], ["k","*","x"], self.dims))

    def test_wrong_sum(self):
        self.assertFalse(check_dimensional_consistency(["F"], ["m","*","m"], self.dims))


if __name__ == "__main__":
    unittest.main()
