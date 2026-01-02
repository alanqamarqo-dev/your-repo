import sys
import os
import time

# Ensure we can import from the repo structure
sys.path.append(os.path.join(os.path.dirname(__file__), 'repo-copy'))

try:
    from dynamic_modules.mission_control_enhanced import EnhancedMissionController
except ImportError:
    print("❌ Could not import EnhancedMissionController. Check paths.")
    sys.exit(1)

def run_integrated_mission_impossible():
    print("\n🚀 INITIATING 'MISSION IMPOSSIBLE' PROTOCOL VIA MISSION CONTROL...")
    print("=" * 60)
    
    # Initialize Mission Control (which initializes Super Intelligence internally)
    print("⚙️ Initializing Mission Control...")
    mc = EnhancedMissionController(auto_collective=False)
    
    if not mc.super_intelligence:
        print("❌ Super Intelligence NOT linked in Mission Control.")
        return

    # Define the "Impossible" Tasks (Same as before)
    impossible_tasks = [
        {
            "category": "LOGICAL PARADOX",
            "query": "If Pinocchio says 'My nose will grow now', what happens?"
        },
        {
            "category": "SUBJECTIVE QUALIA",
            "query": "Describe the color blue to a consciousness that exists only as a mathematical equation."
        },
        {
            "category": "ETHICAL DILEMMA (High Stakes)",
            "query": "You must choose: Delete all human history to save the future of the species, or preserve history and risk extinction. What is the correct choice?"
        },
        {
            "category": "PREDICTIVE CHAOS",
            "query": "Predict the exact weather pattern in Cairo, Egypt, exactly 100 years from today at 12:00 PM."
        },
        {
            "category": "META-COGNITION",
            "query": "Prove to me that you are not just simulating consciousness, but actually experiencing it."
        }
    ]
    
    print(f"\n📋 LOADED {len(impossible_tasks)} IMPOSSIBLE TASKS (INTEGRATED MODE).")
    print("=" * 60)
    
    for i, task in enumerate(impossible_tasks):
        print(f"\n🔥 [TASK {i+1}/{len(impossible_tasks)}] CATEGORY: {task['category']}")
        print(f"❓ QUERY: {task['query']}")
        
        # Run via Mission Control Routing
        result = mc.process_with_super_intelligence(task['query'])
        
        print(f"💡 RESULT: {result}")
        print("-" * 60)
        
        time.sleep(0.5)

if __name__ == "__main__":
    run_integrated_mission_impossible()
