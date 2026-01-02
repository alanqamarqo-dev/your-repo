import asyncio
import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from autonomous_agent import AutonomousAgent

class ResonanceRepairAgent(AutonomousAgent):
    """
    نسخة مخصصة من الوكيل المستقل تركز حصرياً على الإصلاح والصيانة.
    """
    def __init__(self):
        super().__init__()
        print("\n🔧 **Resonance Repair Mode Activated** 🔧")
        print("   - Forcing 'maintenance' goals.")
        print("   - Targeting high-dissonance files.")
        
    async def run_loop(self, cycles=5, duration_minutes=None):
        # نلغي عمل محرك الإرادة العشوائي ونجبره على الصيانة فقط
        self.volition.generate_goal = lambda: {
            "description": "Continuous Resonance Refactoring",
            "type": "maintenance",
            "reason": "User requested immediate system repairs (Priority: High)"
        }
        await super().run_loop(cycles, duration_minutes)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # دورة واحدة فقط للتحقق
    cycles_to_run = 1
    
    print(f"🚀 Starting Resonance Repair Agent for {cycles_to_run} cycles...")
    agent = ResonanceRepairAgent()
    asyncio.run(agent.run_loop(cycles=cycles_to_run))
