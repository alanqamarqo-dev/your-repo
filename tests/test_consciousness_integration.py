
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
sys.modules['psutil'].virtual_memory.return_value.percent = 50.0

# Import the agent
try:
    from autonomous_agent import AutonomousAgent
except ImportError:
    sys.path.append(os.path.join(current_dir, '..'))
    from autonomous_agent import AutonomousAgent

class TestConsciousnessIntegration(unittest.TestCase):
    
    def setUp(self):
        self.agent = AutonomousAgent()
        
    @patch('autonomous_agent.VolitionEngine')
    def test_defining_moment_recording(self, MockVolition):
        """Test if structural evolution triggers a defining moment in consciousness."""
        print("\n🧪 Testing Consciousness Integration (Defining Moment)...")
        
        # 1. Mock Volition to trigger evolution
        self.agent.volition.generate_goal = MagicMock(return_value={
            "description": "Test Evolution",
            "type": "structural_evolution",
            "reason": "Testing Consciousness"
        })
        
        # 2. Mock Unified System & Consciousness
        mock_unified = MagicMock()
        mock_consciousness = MagicMock()
        mock_memory = MagicMock()
        
        mock_consciousness.autobiographical_memory = mock_memory
        mock_unified.consciousness = mock_consciousness
        
        # Inject mock system into agent controller
        self.agent.controller.unified_system = mock_unified
        
        # 3. Mock SelfEngineer
        with patch('Learning_System.Self_Engineer.SelfEngineer') as MockEngineer:
            mock_instance = MockEngineer.return_value
            mock_instance.diagnose.return_value = {'gaps': ['gap'], 'suggested_task': 'evolve'}
            mock_instance.propose.return_value = [MagicMock(id='c1')]
            
            # Run Loop
            asyncio.run(self.agent.run_loop(cycles=1))
            
            # 4. Assertions
            # Check if record_moment was called with 'defining' type
            mock_memory.record_moment.assert_called()
            call_args = mock_memory.record_moment.call_args
            
            self.assertEqual(call_args[0][0], 'defining')
            self.assertIn("Self-Directed Structural Evolution", call_args[0][1]['event'])
            
            print("   ✅ Defining Moment recorded successfully!")
            print(f"      Event: {call_args[0][1]['event']}")
            print(f"      Significance: {call_args[0][1]['significance']}")

if __name__ == '__main__':
    unittest.main()
