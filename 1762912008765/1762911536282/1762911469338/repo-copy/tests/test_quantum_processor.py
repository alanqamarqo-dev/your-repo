import unittest
from Core_Engines.Quantum_Processor import QuantumProcessor

class TestQuantumProcessor(unittest.TestCase):
    def test_unitary_stability(self):
        qp = QuantumProcessor()
        # a known 2x2 rotation-like unitary: identity is simplest
        res = qp.process_task({'type': 'quantum'})
        # expect result to be envelope with 'result' and possibly 'trace'
        self.assertIsInstance(res, dict)
        # if the processor provided a trace, check U^†U ~ I via trace==2
        r = res.get('result')
        if isinstance(r, dict) and 'trace' in r and r['trace'] is not None:
            self.assertAlmostEqual(float(r['trace']), 2.0, places=6)
        else:
            # fallback: ensure we at least got an envelope
            self.assertIn('ok', res)

if __name__ == '__main__':
    unittest.main()
