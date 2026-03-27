
import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock, patch

# Add repo-copy to path
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(current_dir, '..', 'repo-copy')
if repo_copy_dir not in sys.path:
    sys.path.insert(0, repo_copy_dir)

# Mock modules that might be missing or heavy
sys.modules['psutil'] = MagicMock()
# Fix: Ensure virtual_memory().percent returns a float for comparison
sys.modules['psutil'].virtual_memory.return_value.percent = 50.0

# Import the agent
try:
    from autonomous_agent import AutonomousAgent
except ImportError:
    # If running from tests dir, adjust path
    sys.path.append(os.path.join(current_dir, '..'))
    from autonomous_agent import AutonomousAgent

class TestAutonomousIntegration(unittest.TestCase):
    
    def setUp(self):
        # Suppress prints during tests
        self.agent = AutonomousAgent()
        
    @patch('autonomous_agent.VolitionEngine')
    def test_structural_evolution_trigger(self, MockVolition):
        """Test if the agent correctly triggers the new structural evolution action."""
        print("\n🧪 Testing Structural Evolution Integration...")
        
        # Mock Volition to return our specific new goal type
        self.agent.volition.generate_goal = MagicMock(return_value={
            "description": "Test Evolution",
            "type": "structural_evolution",
            "reason": "Testing Integration"
        })
        
        # Mock the SelfEngineer inside the loop (since it's imported inside the method)
        with patch('Learning_System.Self_Engineer.SelfEngineer') as MockEngineer:
            # Setup mock engineer behavior
            mock_instance = MockEngineer.return_value
            mock_instance.diagnose.return_value = {'gaps': ['test_gap'], 'suggested_task': 'test_task'}
            mock_instance.propose.return_value = [MagicMock(id='cand_1')]
            
            # Run 1 cycle
            asyncio.run(self.agent.run_loop(cycles=1))
            
            # Assertions
            # 1. Check if diagnose was called
            mock_instance.diagnose.assert_called()
            print("   ✅ Diagnose called successfully")
            
            # 2. Check if propose was called
            mock_instance.propose.assert_called()
            print("   ✅ Propose called successfully")
            
            # 3. Check memory log
            found_log = any("Structural Evolution generated" in mem for mem in self.agent.memory)
            self.assertTrue(found_log)
            print("   ✅ Memory log updated correctly")

if __name__ == '__main__':
    unittest.main()
