import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure repo-copy is in path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'repo-copy'))

from Core_Engines.Dreaming_Cycle import DreamingEngine

class TestGeneralizationIntegration(unittest.TestCase):

    @patch('Core_Engines.Dreaming_Cycle.infer_ohm_to_power')
    @patch('Core_Engines.Dreaming_Cycle.infer_rc_tau')
    @patch('Core_Engines.Dreaming_Cycle.requests.post')
    def test_dreaming_cycle_runs_generalization(self, mock_post, mock_infer_rc, mock_infer_ohm):
        # Setup mocks
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"response": "Mocked LLM response"}
        
        # Mock Generalization Matrix returns
        mock_infer_ohm.return_value = {"formula": "P=I^2*R", "confidence": 0.95}
        mock_infer_rc.return_value = {"derived": {"tau": 2.5}}
        
        # Initialize Engine
        engine = DreamingEngine()
        
        # Mock file operations to avoid writing to disk
        engine._save_to_kb = MagicMock()
        
        # Run Cycle
        print("\n--- Starting Dream Cycle Test ---")
        results = engine.run_dream_cycle(duration_seconds=5)
        
        # Verify Results
        print("\n--- Test Results ---")
        for r in results:
            print(r)
            
        # Assertions
        self.assertTrue(any("Derived Power Law" in r for r in results), "Should find Power Law generalization")
        self.assertTrue(any("Derived RC Time Constant" in r for r in results), "Should find RC Time Constant generalization")
        
        # Verify calls
        mock_infer_ohm.assert_called()
        mock_infer_rc.assert_called()
        engine._save_to_kb.assert_called()

if __name__ == '__main__':
    unittest.main()
