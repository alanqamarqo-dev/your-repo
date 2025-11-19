import unittest
import os
from Core_Engines.Mathematical_Brain import MathematicalBrain
from Integration_Layer.Communication_Bus import CommunicationBus
from Integration_Layer.Output_Formatter import OutputFormatter


class TestMathematicalBrainEdgeCases(unittest.TestCase):
    def test_unrecognized_input_returns_fallback(self):
        mb = MathematicalBrain()
        # pass an unsupported object
        res = mb.process_task(None)
        self.assertIsInstance(res, dict)
        self.assertFalse(res.get('error'))

    def test_differential_keyword_boost(self):
        mb = MathematicalBrain()
        res = mb.process_task('حل تفاضلية من الدرجة الثانية')
        self.assertTrue(res.get('ok'))
        self.assertGreaterEqual(res.get('confidence', 0.0), 0.9)


class TestCommunicationAndFormatter(unittest.TestCase):
    def test_coordinate_empty_partial_solutions(self):
        cb = CommunicationBus()
        combined = cb.coordinate_components({}, purpose='integration')
        self.assertIsInstance(combined, dict)
        self.assertEqual(combined.get('confidence'), 0.0)

    def test_output_formatter_handles_error_blocks(self):
        fmt = OutputFormatter()
        bad_block = {'error': 'something failed'}
        safe = fmt._safe_engine_block(bad_block)
        self.assertEqual(safe['status'], 'error')


if __name__ == '__main__':
    unittest.main()
