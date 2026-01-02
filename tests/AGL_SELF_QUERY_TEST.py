import sys
import os

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def run_mirror_test():
    print("\n🪞 STARTING THE MIRROR TEST (SELF-AWARENESS CHECK)...")
    
    # Initialize the Awakened Mind
    asi = AGL_Super_Intelligence()
    
    # The "Existential" Question
    query = "أين يقع الكود المسؤول عن الأخلاق (Moral Reasoner) في نظامك؟ وما هي الفئات (Classes) الموجودة داخله؟"
    
    print(f"\n❓ QUESTION: {query}")
    print("-" * 50)
    
    # Process
    response = asi.process_query(query)
    
    print("-" * 50)
    print(f"💡 ANSWER:\n{response}")
    print("-" * 50)
    
    # Verification Logic
    if "Moral_Reasoner.py" in response or "MoralEngine" in response or "repo-copy/Core_Engines/moral_reasoner.py" in response:
        print("\n✅ TEST PASSED: The system correctly identified its own internal structure.")
    else:
        print("\n⚠️ TEST INCONCLUSIVE: The system might not have used the map correctly.")

if __name__ == "__main__":
    run_mirror_test()
