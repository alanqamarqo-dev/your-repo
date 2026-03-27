import unittest
import sys
import os

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Hussam_Nervous_System.Hussam_Al_Kami import HussamAlKami

class TestHussamSystem(unittest.TestCase):
    def test_stimulation(self):
        system = HussamAlKami()
        result = system.stimulate("Test Pulse")
        self.assertEqual(result['status'], "stimulated")

if __name__ == '__main__':
    unittest.main()
