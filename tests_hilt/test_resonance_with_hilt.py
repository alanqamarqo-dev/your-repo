import unittest
import sys
import os
import random

# Add repo-copy to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'repo-copy'))

from Core_Engines.Resonance_Optimizer import ResonanceOptimizer

class TestResonanceWithHILT(unittest.TestCase):
    def test_optimizer_decision_making(self):
        """Compare decision making with and without HILT."""
        
        # Problem: Escape a local minimum
        # Current Score: 100
        # Candidate Score: 95 (Worse)
        # Barrier: 5
        current = 100
        candidate = 95
        
        # 1. Old Optimizer (Porosity = 0)
        old_opt = ResonanceOptimizer()
        old_opt.heikal_porosity = 0.0
        
        # Calculate Probability directly
        delta_E = candidate - current
        barrier_height = abs(delta_E)
        prob_old = old_opt._heikal_tunneling_prob(delta_E, barrier_height)
            
        # 2. New Optimizer (Porosity = 1.5)
        new_opt = ResonanceOptimizer()
        new_opt.heikal_porosity = 1.5
        
        prob_new = new_opt._heikal_tunneling_prob(delta_E, barrier_height)
            
        print(f"Old Probability: {prob_old:.6f}")
        print(f"New Probability: {prob_new:.6f}")
        
        # Improvement should be positive
        self.assertGreater(prob_new, prob_old)

if __name__ == '__main__':
    unittest.main()
