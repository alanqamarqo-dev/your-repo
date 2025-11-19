import unittest


class TestSelfEngineerSmoke(unittest.TestCase):
    def test_quick_smoke_runs(self):
        from Learning_System.Self_Engineer import quick_smoke
        out = quick_smoke()
        self.assertIn('winner', out)


if __name__ == '__main__':
    unittest.main()
