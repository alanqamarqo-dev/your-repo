import unittest
import sys
import os
import numpy as np

# Add repo-copy to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'repo-copy'))

from Core_Engines.Resonance_Optimizer import ResonanceOptimizer

class TestHILTTunneling(unittest.TestCase):
    def setUp(self):
        self.optimizer = ResonanceOptimizer(h_bar=1.0, mass=1.0, barrier_width=2.0)
        # Enable HILT
        self.optimizer.heikal_porosity = 1.5
        self.optimizer.lattice_spacing = 0.5

    def test_simple_barrier(self):
        """Test tunneling through a low barrier."""
        # Barrier height = 0.1
        prob = self.optimizer._heikal_tunneling_prob(energy_diff=-0.1, barrier_height=0.1)
        # With HILT, probability should be significant (observed ~0.18)
        print(f"Simple Barrier Prob: {prob}")
        self.assertGreater(prob, 0.15) 

    def test_impossible_barrier(self):
        """Test tunneling through a massive barrier."""
        # Barrier height = 10.0
        prob = self.optimizer._heikal_tunneling_prob(energy_diff=-10.0, barrier_height=10.0)
        print(f"Impossible Barrier Prob: {prob}")
        self.assertLess(prob, 0.01)

    def test_porosity_effect(self):
        """Test that higher porosity (coherence) increases tunneling."""
        delta_E = -1.0
        barrier = 1.0
        
        # Low Porosity
        self.optimizer.heikal_porosity = 0.1
        prob_low = self.optimizer._heikal_tunneling_prob(delta_E, barrier)
        
        # High Porosity
        self.optimizer.heikal_porosity = 2.0
        prob_high = self.optimizer._heikal_tunneling_prob(delta_E, barrier)
        
        print(f"Low Porosity Prob: {prob_low}")
        print(f"High Porosity Prob: {prob_high}")
        self.assertGreater(prob_high, prob_low)

if __name__ == '__main__':
    unittest.main()
