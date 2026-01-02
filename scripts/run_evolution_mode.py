import asyncio
import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from autonomous_agent import AutonomousAgent

class EvolutionAgent(AutonomousAgent):
    """
    وكيل التطور: يركز على تحسين الخوارزميات والمنطق بدلاً من مجرد الصيانة.
    """
    def __init__(self):
        super().__init__()
        print("\n🧬 **Evolution Mode Activated** 🧬")
        print("   - Goal: Algorithmic Evolution & Optimization.")
        print("   - Target: Mathematical_Brain (Logic Improvement).")
        
    async def run_loop(self, cycles=1, duration_minutes=None):
        # نجبر النظام على هدف تطويري صعب
        self.volition.generate_goal = lambda: {
            "description": "Analyze and optimize Mathematical_Brain.py logic for better performance",
            "type": "self_improvement",
            "reason": "Transitioning from maintenance to active evolution phase."
        }
        
        # نقوم بتعديل بسيط في الذاكرة لنخبره أننا في وضع التطور
        self.memory.append("SYSTEM_MODE: EVOLUTION. Permission granted to rewrite logic for optimization.")
        
        await super().run_loop(cycles, duration_minutes)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    print(f"🚀 Starting Evolution Agent...")
    agent = EvolutionAgent()
    asyncio.run(agent.run_loop(cycles=1))
