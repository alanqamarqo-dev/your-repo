import asyncio
import sys
import os
from unittest.mock import MagicMock

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

# Import the agent
from autonomous_agent import AutonomousAgent

async def run_test():
    print("🧪 Starting Resonance Cycle Test...")
    
    # Initialize Agent
    agent = AutonomousAgent()
    
    # Mock Volition to force maintenance
    agent.volition.generate_goal = MagicMock(return_value={
        "description": "Perform Resonance Refactoring on Dissonant Files",
        "type": "maintenance",
        "reason": "User Request for Faster Repairs"
    })
    
    # Run for 1 cycle
    print("🚀 Running 1 Cycle...")
    await agent.run_loop(cycles=1)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_test())
