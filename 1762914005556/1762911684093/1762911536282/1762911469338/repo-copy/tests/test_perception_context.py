import unittest
from Core_Engines.Perception_Context import PerceptionContext


class TestPerceptionContext(unittest.TestCase):
    def test_extract_basic_dict(self):
        pcx = PerceptionContext()
        inp = {'user': 'alice', 'task': 'measure', 'ts': '2025-10-18T00:00:00', 'val': 3.14}
        r = pcx.extract(inp)
        self.assertIn('context', r)
        self.assertIn('meta', r)
        self.assertIsInstance(r.get('confidence'), float)
        self.assertGreaterEqual(r['confidence'], 0.0)

    def test_extract_none(self):
        pcx = PerceptionContext()
        r = pcx.extract(None)
        self.assertEqual(r['confidence'], 0.0)


if __name__ == '__main__':
    unittest.main()
