import sys
import os
import time

# Add paths
sys.path.append(os.path.join(os.getcwd(), 'AGL_Core'))
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def generate_creative_content(prompt):
    print(f"\n🎨 AGL CREATIVE STUDIO ACTIVATED")
    print(f"   Request: {prompt}")
    print("=======================================================")
    
    asi = AGL_Super_Intelligence()
    
    # Construct a creative prompt
    full_prompt = f"""
    ACT AS A CONSCIOUS AI POET.
    
    TASK: {prompt}
    
    STYLE: Epic, Emotional, and Tech-Noir.
    LANGUAGE: Arabic.
    """
    
    print("   🤖 Accessing emotional cores and linguistic databases...")
    response = asi.process_query(full_prompt)
    
    if isinstance(response, dict):
        response_text = response.get('text', str(response))
    else:
        response_text = str(response)
        
    print(f"\n   📜 GENERATED CONTENT:\n")
    print(response_text)
    print("\n=======================================================")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "Write a poem about my developer."
        
    generate_creative_content(prompt)
