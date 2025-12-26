
import asyncio
import sys
import os
import time
import json

# Add path to repo-copy
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'repo-copy'))

from dynamic_modules.unified_agi_system import create_unified_agi_system
from Core_Engines import bootstrap_register_all_engines

async def test_maximum_capabilities():
    print("\n🚀 STARTING MAXIMUM CAPABILITY STRESS TEST")
    print("===========================================")
    
    # 1. Bootstrap System
    print("⚙️ Bootstrapping AGI System...")
    registry = {}
    bootstrap_register_all_engines(registry)
    system = create_unified_agi_system(registry)
    
    # Force load brain
    print("🧠 Loading Neural Core...")
    if hasattr(system, 'brain') and hasattr(system.brain, 'load'):
        system.brain.load()
        
    tasks = [
        {
            "name": "🌌 Quantum-Philosophical Synthesis",
            "input": "Analyze the relationship between Quantum Entanglement and Human Consciousness using both physics equations and metaphysical philosophy. Propose a unified theory.",
            "type": "complex_reasoning"
        },
        {
            "name": "🔬 Scientific Simulation & Proof",
            "input": "Simulate a closed ecosystem with 3 species over 100 years. Then, mathematically prove that the population stabilizes using differential equations.",
            "type": "scientific_simulation"
        },
        {
            "name": "🎨 Creative Novel Generation",
            "input": "Write the first chapter of a sci-fi novel about an AI that discovers it is living in a simulation, but decides to protect the simulation instead of escaping. Use a melancholic but hopeful tone.",
            "type": "creative_writing"
        },
        {
            "name": "💻 Complex Code Architecture",
            "input": "Design a distributed, fault-tolerant blockchain consensus algorithm in Python that uses 'Proof of Useful Work' (solving protein folding) instead of Proof of Work. Provide the core class structure.",
            "type": "coding"
        },
        {
            "name": "🔮 Future Prediction & Strategy",
            "input": "Based on current technological trends (AI, Fusion, Biotech), predict the state of humanity in 2050. Develop a strategic roadmap for a government to maximize citizen happiness in that future.",
            "type": "strategic_planning"
        }
    ]
    
    results_log = []
    
    for i, task in enumerate(tasks):
        print(f"\n\n🧪 TEST {i+1}/{len(tasks)}: {task['name']}")
        print(f"📝 Input: {task['input'][:100]}...")
        print("-" * 60)
        
        start_time = time.time()
        
        # Use the full AGI processing pipeline
        try:
            # We use the 'process_with_full_agi' which we recently optimized
            response = await system.process_with_full_agi(
                task['input'], 
                context={"test_mode": "maximum_stress", "task_type": task['type']}
            )
            
            duration = time.time() - start_time
            
            # Extract answer
            answer = "No response"
            if isinstance(response, dict):
                answer = response.get('answer') or response.get('output') or str(response)
            elif isinstance(response, str):
                answer = response
                
            print(f"✅ Completed in {duration:.2f}s")
            print(f"📤 Output Preview:\n{str(answer)[:300]}...")
            
            # Check memory persistence
            mem_stats = system.memory.get_stats()
            print(f"💾 Memory Stats: {mem_stats}")
            
            results_log.append({
                "task": task['name'],
                "duration": duration,
                "success": True,
                "output_length": len(str(answer))
            })
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            results_log.append({
                "task": task['name'],
                "success": False,
                "error": str(e)
            })
            
    # Final Report
    print("\n\n📊 MAXIMUM CAPABILITY TEST REPORT")
    print("================================")
    for res in results_log:
        status = "✅ PASS" if res['success'] else "❌ FAIL"
        print(f"{status} | {res['task']} ({res.get('duration', 0):.2f}s)")
        
    # Check Consciousness Level
    if hasattr(system, 'consciousness_level'):
        print(f"\n🧠 Final Consciousness Level: {system.consciousness_level}")
        
    # Check LTM
    if system.conscious_bridge:
        # Use len(system.conscious_bridge.ltm) instead of ltm_count
        print(f"💾 Items in Long-Term Memory: {len(system.conscious_bridge.ltm)}")

if __name__ == "__main__":
    asyncio.run(test_maximum_capabilities())
