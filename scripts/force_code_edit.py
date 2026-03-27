
import asyncio
import sys
import os
from unittest.mock import MagicMock

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

# Import the agent
from autonomous_agent import AutonomousAgent

async def run_force_test():
    print("🧪 Starting Forced Self-Improvement Test...")
    
    # Initialize Agent
    agent = AutonomousAgent()
    
    # Mock Volition to force the 'improve_code' action
    # We use a goal description that contains "optimize" to trigger the logic in autonomous_agent.py
    agent.volition.generate_goal = MagicMock(return_value={
        "description": "Optimize Volition_Engine logic to be more creative and efficient.",
        "type": "improvement",
        "reason": "User Forced Test"
    })
    
    # Run for 1 cycle
    print("🚀 Running 1 Cycle with FORCED GOAL...")
    await agent.run_loop(cycles=1)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_force_test())
