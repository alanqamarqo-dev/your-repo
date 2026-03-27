import asyncio
import sys
import os

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
if repo_copy_dir not in sys.path:
    sys.path.insert(0, repo_copy_dir)

import agl_paths
agl_paths.setup_sys_path()

# Import the agent
from autonomous_agent import AutonomousAgent

async def main():
    print("\n🤖 --- LAUNCHING AUTONOMOUS AGENT (10 MINUTE RUN) --- 🤖")
    print("   This agent uses the PROVEN Neuro-Symbolic Architecture.")
    print("   It will autonomously generate goals, reason, and execute tasks.")
    print("   (Press Ctrl+C to stop early)\n")
    
    agent = AutonomousAgent()
    
    # Run for 10 minutes
    await agent.run_loop(duration_minutes=10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 User stopped the agent.")
