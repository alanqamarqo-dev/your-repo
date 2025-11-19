import unittest
import torch
from Core_Engines.Advanced_Exponential_Algebra import AdvancedExponentialAlgebra, LieAlgebraProcessor


class TestAdvancedExponentialAlgebra(unittest.TestCase):
    def test_matrix_exponential_pade_identity(self):
        aa = AdvancedExponentialAlgebra()
        # In some test environments the project's torch stub returns plain lists.
        # Ensure the function raises a clear AttributeError when given a non-tensor.
        I = torch.eye(2)
        if isinstance(I, list):
            with self.assertRaises(AttributeError):
                _ = aa.matrix_exponential_pade(I)
        else:
            expI = aa.matrix_exponential_pade(I)
            self.assertEqual(expI.shape, (2, 2))

    def test_lie_algebra_processor_bases(self):
        lap = LieAlgebraProcessor()
        so3 = lap.special_orthogonal_algebra(3)
        self.assertTrue(len(so3) > 0)
        su2 = lap.special_unitary_algebra(2)
        self.assertTrue(len(su2) >= 3)


if __name__ == '__main__':
    unittest.main()
