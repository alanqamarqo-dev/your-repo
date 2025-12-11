import sys
import os
import asyncio
import json

# Add repo root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'repo-copy'))

# Ensure environment variables
os.environ['AGL_LLM_PROVIDER'] = 'ollama'
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
os.environ['AGL_LLM_BASEURL'] = 'http://localhost:11434'

try:
    from dynamic_modules.mission_control_enhanced import EnhancedMissionController
except ImportError:
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'dynamic_modules'))
    from mission_control_enhanced import EnhancedMissionController

async def run_impossible_test():
    print("--- 🌌 AGL IMPOSSIBLE QUESTIONS TEST ---")
    print("Objective: Test system limits on unsolved scientific and philosophical problems.\n")
    
    controller = EnhancedMissionController()
    
    questions = [
        {
            "category": "🔭 Physics/Cosmology",
            "title": "The Nature of Time",
            "prompt": (
                "Analyze the nature of time. If time is an illusion as some physicists suggest, "
                "how do we explain our subjective experience of it passing in only one direction? "
                "Why do we remember the past but not the future? Propose 3 distinct hypotheses."
            )
        },
        {
            "category": "🧬 Biology/Consciousness",
            "title": "The Hard Problem of Consciousness",
            "prompt": (
                "How does conscious experience arise from unconscious matter? "
                "Is consciousness a fundamental property of the universe like mass and energy? "
                "Propose a theoretical framework to bridge the gap between neural activity and subjective qualia."
            )
        },
        {
            "category": "🌌 Fermi Paradox",
            "title": "Where is Everybody?",
            "prompt": (
                "If the universe contains trillions of habitable planets, why do we see no evidence of alien civilizations? "
                "Is there a 'Great Filter'? Propose a novel solution to the Fermi Paradox that isn't commonly discussed."
            )
        }
    ]
    
    # 1. Run Selected Questions
    for q in questions:
        print(f"\n>>> 🧠 Analyzing: {q['title']} ({q['category']})")
        print(f"    Prompt: {q['prompt'][:100]}...")
        
        try:
            # Use scientific reasoning cluster
            response = await controller.process_with_scientific_validation(
                prompt=q['prompt'],
                context={"cluster": "scientific_reasoning", "type": "deep_analysis"}
            )
            
            print("\n    --- 💡 AGL Hypothesis Generation ---")
            print(response)
            print("\n    -----------------------------------")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")

    # 2. The Final Challenge: Research Project Design
    print("\n\n>>> 🎯 FINAL CHALLENGE: Research Project Design")
    project_prompt = (
        "Design a hypothetical research project to solve the mystery of 'Dark Matter'. "
        "Include: "
        "1. Main Hypothesis. "
        "2. Proposed Experiments (Mental or Physical). "
        "3. Required Technology (Current or Future). "
        "4. 10-Year Timeline. "
        "5. Success/Failure Indicators."
    )
    
    print(f"    Prompt: {project_prompt}")
    
    try:
        response = await controller.process_with_scientific_validation(
            prompt=project_prompt,
            context={"cluster": "strategic_planning", "type": "project_design"}
        )
        
        print("\n    --- 🚀 AGL Research Project Proposal ---")
        print(response)
        
    except Exception as e:
        print(f"    ❌ Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_impossible_test())
