import unittest
import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'repo-copy'))

from Core_Engines.Heikal_Hybrid_Logic import HeikalHybridLogicCore

class TestHybridReasoning(unittest.TestCase):
    def setUp(self):
        self.core = HeikalHybridLogicCore()

    def test_superposition_creation(self):
        """Test creating a superposition state."""
        prop = self.core.add_proposition("Idea", initial_prob=1.0) # True
        prop.apply_hadamard() # Superposition
        
        # Probability of True should be 0.5
        prob_true = abs(prop.alpha)**2
        self.assertAlmostEqual(prob_true, 0.5)

    def test_entanglement(self):
        """Test entanglement of two ideas."""
        p1 = self.core.add_proposition("A", 1.0)
        p2 = self.core.add_proposition("B", 0.0)
        
        # Entangle
        self.core.entangle("A", "B")
        
        # They should have same state now
        self.assertAlmostEqual(p1.alpha, p2.alpha)
        self.assertAlmostEqual(p1.beta, p2.beta)

if __name__ == '__main__':
    unittest.main()
