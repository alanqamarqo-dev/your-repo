import sys
import os
import time

# --- Path Setup ---
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
if repo_copy_dir not in sys.path:
    sys.path.insert(0, repo_copy_dir)

from Core_Engines.self_critique_and_revise import SelfCritiqueAndRevise
from Core_Engines import bootstrap_register_all_engines
from Integration_Layer.integration_registry import registry

def main():
    print("🚀 Initializing General Purpose Critic Test...")
    
    # Bootstrap to ensure Hosted_LLM is available for the critic to use
    # We pass the global registry so SelfCritiqueAndRevise can find the engines
    bootstrap_register_all_engines(registry, allow_optional=True, max_seconds=30)
    
    critic_engine = SelfCritiqueAndRevise()
    
    # A "weak" draft answer
    weak_draft = "الزمن هو مجرد ساعة تدور. والوعي هو أننا نعرف الوقت. لذا القرار يعتمد على الساعة."
    
    print(f"\n📝 Weak Draft:\n{weak_draft}\n")
    print("-" * 50)
    print("⏳ Critiquing and Revising...")
    
    start_time = time.time()
    result = critic_engine.process_task({"draft": weak_draft})
    duration = time.time() - start_time
    
    print(f"✅ Done in {duration:.2f} seconds.\n")
    
    print("🔍 Critique:")
    print(result.get('critique', 'No critique generated'))
    print("-" * 50)
    
    print("✨ Revised Answer:")
    print(result.get('revised', 'No revision generated'))
    print("-" * 50)

if __name__ == "__main__":
    main()
