
import sys
import os
import asyncio
import json

# Add root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

async def main():
    print("🚀 Starting Self-Improvement Scenario Test...")
    
    # 1. Import Self-Improvement Engine
    print("   ⚙️ Importing SelfImprovementEngine...")
    try:
        from Self_Improvement.Self_Improvement_Engine import SelfImprovementEngine
        engine = SelfImprovementEngine()
        print("   ✅ Imported SelfImprovementEngine successfully.")
    except ImportError:
        print("   ⚠️ Could not import SelfImprovementEngine directly.")
        try:
            from Self_Improvement.Self_Improvement_Engine import SelfLearningManager
            engine = SelfLearningManager()
            print("   ✅ Imported SelfLearningManager as fallback.")
        except ImportError as e:
            print(f"   ❌ Failed to import any self-improvement class: {e}")
            return

    # 2. Import Self-Monitoring System
    print("   ⚙️ Importing SelfMonitoringSystem...")
    try:
        from Self_Improvement.Self_Monitoring_System import SelfMonitoringSystem
        monitor = SelfMonitoringSystem()
        print("   ✅ Imported SelfMonitoringSystem successfully.")
    except ImportError as e:
        print(f"   ❌ Failed to import SelfMonitoringSystem: {e}")
        monitor = None

    # 3. Simulate a weakness/failure
    print("\n   🧪 Simulating a weakness (Low Performance in 'Quantum Reasoning')...")
    
    # Log a failure event
    if hasattr(engine, 'record'):
        engine.record(key="quantum_reasoning_accuracy", reward=0.2, note="Failed to solve complex entanglement problem")
        print("   📝 Recorded low reward (0.2) for 'quantum_reasoning_accuracy'")
    
    # 4. Trigger Improvement Cycle
    print("\n   🔄 Triggering Improvement Cycle...")
    
    # Enable self learning env var for this test
    os.environ["AGL_SELF_LEARNING_ENABLE"] = "1"
    
    if hasattr(engine, 'run_training_epoch'):
        result = engine.run_training_epoch()
        print(f"   📊 Training Epoch Result: {result}")
    elif hasattr(engine, 'improve'):
        result = engine.improve()
        print(f"   📊 Improve Result: {result}")
        
    # 5. Check for generated artifacts (Learning Curve)
    print("\n   🔎 Checking artifacts...")
    artifacts_path = os.path.join("artifacts", "learning_curve.json")
    if os.path.exists(artifacts_path):
        print(f"   ✅ Found learning_curve.json")
        try:
            with open(artifacts_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    last_entry = data[-1]
                    print(f"   📈 Last Entry: Epoch {last_entry.get('epoch')}, Avg Reward: {last_entry.get('avg_reward')}")
        except Exception as e:
            print(f"   ⚠️ Error reading learning curve: {e}")
    else:
        print("   ⚠️ learning_curve.json not found (might be first run or disabled)")

    # 6. Check Self-Monitoring Analysis
    if monitor:
        print("\n   🩺 Running Self-Monitoring Analysis...")
        performance_data = {'score': 0.4, 'domain': 'quantum'}
        analysis = monitor.analyze_performance(performance_data)
        print(f"   📊 Analysis: {analysis}")
        
        if analysis.get('needs_improvement'):
            print("   ✅ System correctly identified need for improvement.")
        else:
            print("   ⚠️ System did NOT identify need for improvement.")

    print("\n   🏁 Test finished.")

if __name__ == "__main__":
    asyncio.run(main())
