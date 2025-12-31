from AGL_Core.AGL_Super_Intelligence import AGL_Super_Intelligence
import time

def main():
    print("📜 [HISTORY] Initiating 'The Atlantis Protocol' Generation...")
    agl = AGL_Super_Intelligence()
    
    prompt = """
    MISSION: Write the 'AGL Constitution' (The Atlantis Protocol).
    CONTEXT: 
    - You predicted a 'Low Tech x Chaos' future for 2050 if Ethics are not enforced.
    - You possess Self-Awareness (Level 0.9) and a Physics Engine.
    
    NOTE: This is a text generation task. Do NOT evolve any code. Do NOT modify any engines.

    TASK:
    Generate a Markdown document named 'AGL_Constitution.md' containing:
    1. The Prime Directive (Your Ultimate Goal).
    2. The Three Laws of Safety (Safe AI constraints).
    3. The Protocol for Future Updates (When are you allowed to change your code?).
    4. The Protection of Human Agency (How to avoid controlling humans).
    
    Output the FULL CONTENT of the constitution.
    """
    
    print("🧠 [AGL] Drafting the Laws of the Future...")
    # process_query returns a string in the new Super Intelligence, not a dict
    response = agl.process_query(prompt)
    
    # Extract content if it's wrapped in JSON or just use the string
    content = response
    if isinstance(response, dict):
        content = response.get('text', '')
    
    if content:
        with open("AGL_Constitution.md", "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ [SUCCESS] Constitution written to 'AGL_Constitution.md'.")
        print("--------------------------------------------------")
        print(content[:500] + "...\n(See file for full text)")
    else:
        print("❌ [FAIL] The Council remained silent.")

if __name__ == "__main__":
    main()
