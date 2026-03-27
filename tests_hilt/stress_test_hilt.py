import unittest
import sys
import os
import time

# Add repo-copy to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'repo-copy'))

from Core_Engines.Resonance_Optimizer import ResonanceOptimizer

class StressTestHILT(unittest.TestCase):
    def test_under_heavy_load(self):
        """Test optimizer under heavy load (10,000 iterations)."""
        optimizer = ResonanceOptimizer()
        optimizer.heikal_porosity = 1.5 # Enable HILT
        
        start_time = time.time()
        
        success_count = 0
        iterations = 10000
        
        for i in range(iterations):
            # Randomize problem
            current = 100
            candidate = 100 - (i % 20) # Varying barrier heights
            
            try:
                accepted, _ = optimizer.optimize_search(current, candidate)
                if accepted: success_count += 1
            except Exception as e:
                self.fail(f"Crashed at iteration {i}: {e}")
                
        duration = time.time() - start_time
        print(f"Processed {iterations} iterations in {duration:.4f}s")
        print(f"Success Rate: {success_count/iterations:.4f}")
        
        # Performance check: Should be fast
        self.assertLess(duration, 5.0) # Should take less than 5 seconds

if __name__ == '__main__':
    unittest.main()
