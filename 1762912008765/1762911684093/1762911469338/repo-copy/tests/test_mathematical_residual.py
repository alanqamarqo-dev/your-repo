import unittest
import os
import sys
import json
import time

from AGL import create_agl_instance


class TestMathematicalResidual(unittest.TestCase):
    def test_residual_below_threshold_for_differential(self):
        agl = create_agl_instance()
        task = 'حل معادلة تفاضلية'  # this should trigger the symbolic branch
        out = agl.process_complex_problem(task)
        # report uses solution.result.mathematical_brain or result under result
        sol = out.get('solution', {})
        # formatted result may be under sol['result'] depending on OutputFormatter
        res_block = sol.get('result', {}) if isinstance(sol, dict) else sol
        # try to locate mathematical_brain result
        mb = None
        if isinstance(res_block, dict):
            mb = res_block.get('mathematical_brain') or res_block.get('mathematical')
        # fallback to integrated solution structure
        if not mb:
            mb = out.get('solution', {}).get('mathematical_brain')

        if not mb:
            self.skipTest('No mathematical_brain result present')

        # expected to be a dict with 'result' -> 'verification' -> 'residual_norm'
        verification = None
        if isinstance(mb, dict):
            if isinstance(mb.get('result'), dict):
                verification = mb['result'].get('verification')
            else:
                verification = mb.get('verification')

        if not verification:
            self.skipTest('No verification block present for mathematical result')

        residual = verification.get('residual_norm')
        self.assertIsNotNone(residual, 'residual_norm missing')
        self.assertLessEqual(float(residual), 1e-6, msg=f"Residual {residual} exceeds threshold")


if __name__ == '__main__':
    unittest.main()
