import asyncio
import sys
import os

# Mock Heikal to verify integration without full engine load if needed, 
# but here we want to test the actual import.

from autonomous_agent import AutonomousAgent

async def test_integration():
    print("🧪 Testing Autonomous Agent Heikal Integration...")
    
    agent = AutonomousAgent()
    
    if agent.heikal_core and agent.heikal_memory:
        print("✅ Heikal Modules Successfully Attached to Agent.")
    else:
        print("❌ Heikal Modules FAILED to Attach.")
        return

    print("✅ Integration Verified via Inspection.")

if __name__ == "__main__":
    asyncio.run(test_integration())
