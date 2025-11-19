import unittest

from Learning_System.Units_Validator import UnitsValidator


class TestUnitsValidatorLS(unittest.TestCase):
    def test_validate_linear_dataset(self):
        try:
            uv = UnitsValidator()
        except RuntimeError:
            self.skipTest('pint not installed in test environment')

        res = uv.check_equation_units('F = k * x', {'F': 'N', 'k': 'N/m', 'x': 'm'})
        self.assertTrue(res.get('ok'), msg=str(res))


if __name__ == '__main__':
    unittest.main()
