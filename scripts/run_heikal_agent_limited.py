import asyncio
import sys
import os
import time
import requests

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
if repo_copy_dir not in sys.path:
    sys.path.insert(0, repo_copy_dir)

import agl_paths
agl_paths.setup_sys_path()

# Import the agent
from autonomous_agent import AutonomousAgent

def force_vacuum_unload():
    """Forces Ollama to unload the model from VRAM immediately."""
    try:
        url = f"{os.environ.get('AGL_LLM_BASEURL', 'http://localhost:11434')}/api/generate"
        payload = {
            "model": os.environ.get('AGL_LLM_MODEL', 'qwen2.5:7b-instruct'),
            "keep_alive": 0
        }
        requests.post(url, json=payload, timeout=2)
        print("🌌 [Vacuum Protocol]: Model unloaded from VRAM (0% Resource Usage).")
    except Exception as e:
        print(f"⚠️ [Vacuum Warning]: Could not unload model: {e}")

class HeikalVacuumAgent(AutonomousAgent):
    """
    A specialized version of the Autonomous Agent that strictly enforces
    the Heikal Vacuum Protocol (Load -> Think -> Unload).
    """
    async def run_loop(self, cycles=3, duration_minutes=None):
        print(f"🚀 Starting Heikal Vacuum Agent ({cycles} cycles)...")
        print("   Protocol: Materialize -> Execute -> Dematerialize")
        
        for i in range(cycles):
            print(f"\n--- 🔄 Cycle {i+1}/{cycles} ---")
            
            # 1. Run the standard cycle logic (Materialize & Think)
            # We can't easily call super().run_loop because it's a loop.
            # So we'll just call the internal logic if we could, but since we can't,
            # we will rely on the fact that the standard agent doesn't loop if we call it carefully?
            # Actually, let's just copy the critical logic or use the existing run_loop but interrupt it?
            # No, better to just run the standard loop for 1 cycle at a time if possible?
            # The standard run_loop takes 'cycles' arg.
            
            # Let's run the standard agent for 1 cycle, then unload.
            await super().run_loop(cycles=1)
            
            # 2. Dematerialize (Unload)
            print("👻 [Vacuum]: Dematerializing consciousness...")
            force_vacuum_unload()
            
            # Optional: Wait a bit to show the system is cool
            print("💤 [Vacuum]: System is dormant (Cooling down)...")
            await asyncio.sleep(2)

async def main():
    print("\n🤖 --- LAUNCHING HEIKAL VACUUM AGENT --- 🤖")
    print("   This agent respects the 'Vacuum Hosting' protocol.")
    print("   It will NOT hog your system resources.")
    
    agent = HeikalVacuumAgent()
    
    # Run for 3 cycles
    await agent.run_loop(cycles=3)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 User stopped the agent.")
