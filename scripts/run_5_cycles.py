import asyncio
import sys
import os

# Force environment for 7B Model
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
os.environ['AGL_LLM_PROVIDER'] = 'ollama'
os.environ['AGL_LLM_BASEURL'] = 'http://localhost:11434'

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
    print("\n🤖 --- LAUNCHING AUTONOMOUS AGENT (5 CYCLES) --- 🤖")
    
    agent = AutonomousAgent()
    
    # Run for 5 cycles
    await agent.run_loop(cycles=5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 User stopped the agent.")
