import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import asyncio

# Ensure repo-copy is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from autonomous_agent import AutonomousAgent

class TestDreamIntegration(unittest.TestCase):

    @patch('autonomous_agent.emergency_layer')
    @patch('autonomous_agent.DreamingEngine')
    @patch('autonomous_agent.EnhancedMissionController')
    def test_dream_insights_integration(self, MockMissionControl, MockDreamingEngine, MockEmergency):
        # Setup
        agent = AutonomousAgent()
        
        # Mock Emergency to allow dreaming
        MockEmergency.check_status.return_value = True
        
        # Mock Dreaming Engine to return a generalization
        agent.dreaming_engine.run_dream_cycle.return_value = [
            "Generalization: Derived Power Law: P=I^2*R"
        ]
        
        # Mock Consciousness
        mock_consciousness = MagicMock()
        mock_memory = MagicMock()
        mock_consciousness.autobiographical_memory = mock_memory
        agent.controller.unified_system.consciousness = mock_consciousness
        
        # Run the specific block (we can't run the full loop easily, so we'll simulate the end of loop logic)
        # We'll extract the logic into a helper or just copy-paste the logic for the test if we can't refactor.
        # Since I can't refactor the agent easily without breaking things, I will rely on the fact that I just edited the file.
        # But to be rigorous, I should verify the code I wrote is syntactically correct and importable.
        
        # Actually, I can just instantiate the agent and call the logic if I wrap it in a method, 
        # but it's in the run_loop method.
        # I will verify by inspection and by running a "dry run" of the agent if possible, 
        # but running the full agent is heavy.
        
        # Let's try to run a very short loop (0 cycles) if possible, but the logic is AFTER the loop.
        # The loop condition is `while i < cycles`. If I set cycles=0, it skips the loop and goes to dreaming.
        
        async def run_test():
            await agent.run_loop(cycles=0, duration_minutes=0)
            
        asyncio.run(run_test())
        
        # Assertions
        agent.dreaming_engine.run_dream_cycle.assert_called()
        mock_memory.record_moment.assert_called_with(
            'realization',
            {
                "event": "Scientific Discovery (Dream)",
                "content": "Generalization: Derived Power Law: P=I^2*R",
                "significance": "High - New knowledge derived from internal patterns."
            }
        )

if __name__ == '__main__':
    unittest.main()
