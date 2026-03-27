
import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.prompt_composer_v2 import PromptComposerV2

def test_quantum_prompting():
    print("--- Testing Quantum Prompt Composer ---")
    
    composer = PromptComposerV2()
    
    # Case 1: Scientific Query
    task1 = "أريد شرحاً لنظرية الكم وتطبيقاتها"
    res1 = composer.process_task({"task": task1})
    print(f"\n[Task 1]: {task1}")
    print(f"Prompt Preview: {res1['prompt'][:200]}...")
    if "عالم باحث" in res1['prompt']:
        print("✅ Correct Template Selected: Scientific")
    else:
        print("❌ Incorrect Template")
        
    # Case 2: Creative Query
    task2 = "اكتب قصة عن روبوت يحلم"
    res2 = composer.process_task({"task": task2})
    print(f"\n[Task 2]: {task2}")
    print(f"Prompt Preview: {res2['prompt'][:200]}...")
    if "روائي مبدع" in res2['prompt']:
        print("✅ Correct Template Selected: Creative")
    else:
        print("❌ Incorrect Template")

    # Case 3: Strategic Query
    task3 = "ما هي استراتيجية الاستثمار في الذهب؟"
    res3 = composer.process_task({"task": task3})
    print(f"\n[Task 3]: {task3}")
    print(f"Prompt Preview: {res3['prompt'][:200]}...")
    if "مخطط استراتيجي" in res3['prompt']:
        print("✅ Correct Template Selected: Strategic")
    else:
        print("❌ Incorrect Template")

if __name__ == "__main__":
    test_quantum_prompting()
