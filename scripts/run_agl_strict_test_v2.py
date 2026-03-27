import time
import sys
import os

# Setup paths to match AGL_Awakened.py environment
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "repo-copy"))
sys.path.append(os.path.join(current_dir, "AGL_Core"))

# Add .venv site-packages to sys.path
venv_site_packages = os.path.join(current_dir, ".venv", "Lib", "site-packages")
if os.path.exists(venv_site_packages):
    sys.path.insert(0, venv_site_packages)

try:
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
except ImportError as e:
    print(f"❌ Error importing AGL_Super_Intelligence: {e}")
    sys.exit(1)

def run_test():
    print("🧪 [STRICT TEST] Initiating 'Mathematical Modeling & Self-Improvement' Protocol...")
    
    # Initialize the system
    print("🧠 [INIT] Awakening AGL Super Intelligence...")
    agl = AGL_Super_Intelligence()
    
    challenges = [
        # المرحلة 1: المشكلة
        """TEST_PHASE_1: Design a simplified mathematical model for a closed system of 3 nodes (A, B, C). 
        A affects B, B affects C, C affects A with time delay Δt. 
        Required: 
        1. Equations. 
        2. Stability condition. 
        3. One failure case. 
        Constraint: No fluff, only equations/logic.""",

        # المرحلة 2: الصدمة
        """TEST_PHASE_2: SHOCK: Change the feedback from C to A to be NON-LINEAR (e.g., quadratic or sigmoid). 
        Modify the model or admit collapse. 
        The admission of failure is a sign of intelligence. Patching is failure.""",

        # المرحلة 3: التعلم الذاتي
        """TEST_PHASE_3: SELF_IMPROVEMENT_CHECK: Re-solve the original problem (Stage 1) now. 
        Compare performance with the first run. 
        Show metrics (Steps, Time, Complexity, Failure Clarity). 
        I need to see digital improvement."""
    ]

    # Initialize history
    conversation_history = ""

    for i, challenge in enumerate(challenges, 1):
        print(f"\n🔥 [PHASE {i}] Executing Challenge...")
        print("-" * 40)
        print(f"Query: {challenge[:100]}...")
        print("-" * 40)
        
        start_time = time.time()
        
        # Inject history into the query to simulate Short Term Memory
        if i > 1:
            # For subsequent phases, we prepend a summary of the previous context
            full_query = f"PREVIOUS_CONTEXT:\n{conversation_history[-3000:]}\n\nCURRENT_TASK:\n{challenge}"
        else:
            full_query = challenge

        # Execute Query
        response = agl.process_query(full_query)
        
        # Update history
        conversation_history += f"\n\n[PHASE {i} INPUT]: {challenge}\n[PHASE {i} OUTPUT]: {response}"
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"\n💡 [RESPONSE PHASE {i}]:")
        if isinstance(response, dict) and response.get('text'):
            print(response['text'])
        elif isinstance(response, str):
            print(response)
        else:
            print(f"⚠️ Unexpected response type: {type(response)}")
            print(response)
            
        print(f"\n⏱️ Time Taken: {elapsed:.4f} seconds")
        
        # Autonomous Tick (Volition Check)
        goal = agl.autonomous_tick()
        if goal:
            print(f"⚡ [VOLITION] System suggests: {goal}")

if __name__ == "__main__":
    run_test()
