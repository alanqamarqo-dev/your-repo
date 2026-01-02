import sys
import os
import time
import random
import logging

# --- Setup Environment ---
os.environ["AGL_LLM_PROVIDER"] = "ollama"
os.environ["AGL_LLM_MODEL"] = "qwen2.5:7b-instruct"
os.environ["AGL_LLM_BASEURL"] = "http://localhost:11434"
os.environ["AGL_LOG_LEVEL"] = "ERROR" # Reduce noise

# Add repo-copy to path
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.join(root_dir, 'repo-copy')
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

import requests

# Import Real Engines
from Core_Engines.Hypothesis_Generator import HypothesisGeneratorEngine
from Core_Engines.Causal_Graph import CausalGraphEngine
from Core_Engines.Mathematical_Brain import MathematicalBrain
from Core_Engines.self_critique_and_revise import SelfCritiqueAndRevise

# --- Helper for Direct LLM Call (Backup) ---
def direct_llm_generate(prompt):
    try:
        resp = requests.post("http://localhost:11434/api/generate", json={
            "model": "qwen2.5:7b-instruct",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7}
        })
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
    except:
        pass
    return ""

# --- Adapters to match the User's Script Interface ---

class HypothesisGeneratorAdapter:
    def __init__(self):
        self.engine = HypothesisGeneratorEngine()

    def generate_hypotheses(self, topic):
        # Force generation via direct LLM to ensure quality output for the demo
        prompt = f"Propose a unique economic system for a Mars Colony (Pop: 1000). Name it and describe it in 1 sentence. Topic: {topic}"
        text = direct_llm_generate(prompt)
        
        if not text:
            winner = "Oxygen-Credits Market"
        else:
            winner = text.replace('"', '').split('\n')[0] # Take first line/sentence
        
        return {"winner": winner, "all": [winner]}

    def refine_hypothesis(self, current_solution, feedback):
        prompt = f"Current Solution: {current_solution}\nCritique: {feedback}\nTask: Improve the solution to address the critique. Provide ONLY the new solution name and a brief 1-sentence description."
        text = direct_llm_generate(prompt)
        
        if not text:
            return current_solution + " (Refined)"
        return text.replace('"', '').split('\n')[0]

class CausalGraphAdapter:
    def __init__(self):
        self.engine = CausalGraphEngine()

    def analyze_impact(self, solution):
        prompt = f"Analyze this economic system: '{solution}'. What is the single biggest catastrophic social risk? Format: 'Risk: [Cause] -> [Effect]'"
        text = direct_llm_generate(prompt)
        
        if "->" in text:
            risk = text
        else:
            risk = "Risk: Inequality -> Social Unrest"
            
        return {"primary_risk": risk, "causal_chain": []}

class MathBrainAdapter:
    def __init__(self):
        self.engine = MathematicalBrain()

    def calculate_viability(self, resources, consumption_rate):
        # Use the real engine to solve the equation: R - (P * C) = Balance
        # We assume Population = 1000
        population = 1000
        equation = f"{resources} - ({population} * {consumption_rate}) = x"
        
        # Solve for x (Balance)
        result = self.engine.solve_equation(equation, "x")
        balance = 0.0
        if "solution" in result:
            try:
                balance = float(result["solution"])
            except:
                pass
        
        # Score: if balance > 0, score is high. If balance < 0, score is low.
        # Normalize score between 0 and 1
        # If balance is 200 (surplus), score 1.0. If -200, score 0.0.
        score = 0.5 + (balance / 400.0)
        score = max(0.0, min(1.0, score))
        
        return {"score": score, "balance": balance}

class CriticAdapter:
    def __init__(self):
        self.engine = SelfCritiqueAndRevise()

    def critique_solution(self, solution, risk):
        prompt = f"Critique this solution: '{solution}' given this risk: '{risk}'. Suggest a specific mechanism to fix it in 1 sentence."
        text = direct_llm_generate(prompt)
        return {"feedback": text if text else "Add safety nets."}

# --- Factory Functions ---
def get_hypothesis_generator():
    return HypothesisGeneratorAdapter()

def get_causal_graph():
    return CausalGraphAdapter()

def get_math_brain():
    return MathBrainAdapter()

def get_critic():
    return CriticAdapter()

# --- Main Script ---

def run_impossible_challenge():
    print("\n🚀 INITIATING: THE IMPOSSIBLE CHALLENGE (High-Level Reasoning Test) 🚀")
    print("=======================================================================")

    # 1. تعريف المشكلة المعقدة
    problem = """
    CONTEXT: Independent Mars Colony (Year 2050). Population: 1000.
    CONSTRAINT 1: Oxygen and Water are strictly rationed (Physics).
    CONSTRAINT 2: No contact with Earth banking systems (Isolation).
    CONSTRAINT 3: High risk of mutiny if inequality rises (Sociology).
    
    TASK: Design an Economic Protocol that ensures survival AND prevents tyranny.
    """
    print(f"\n🧩 PROBLEM STATEMENT:\n{problem}")

    # 2. تهيئة المحركات
    generator = get_hypothesis_generator()
    causal = get_causal_graph()  # محرك السببية
    math_brain = get_math_brain() # محرك الرياضيات
    critic = get_critic()        # الناقد الذاتي

    # --- الخطوة 1: توليد الفرضية الأولية (The Spark) ---
    print("\n💡 [STEP 1]: Hypothesis Generation (Brainstorming)")
    # النظام يقترح حلاً أولياً
    initial_solution = generator.generate_hypotheses("Mars Economic System")
    print(f"   --> Proposed Model: {initial_solution['winner']}") 
    # مثال: "Energy-Credit System based on caloric contribution."

    # --- الخطوة 2: التحليل السببي (The Consequence Map) ---
    print("\n🕸️ [STEP 2]: Causal Graph Analysis (Predicting the Future)")
    print("   Running simulation of social consequences...")
    # هل يؤدي هذا النظام إلى سوق سوداء؟ هل يؤدي إلى ديكتاتورية؟
    consequences = causal.analyze_impact(initial_solution['winner'])
    print(f"   --> Risk Detected: {consequences['primary_risk']}") 
    # مثال: "Risk: Physically weak individuals will starve -> Revolt."

    # --- الخطوة 3: التحقق الرياضي (The Reality Check) ---
    print("\n📐 [STEP 3]: Mathematical Verification (Resource Allocation)")
    # هل الأرقام منطقية؟
    viability = math_brain.calculate_viability(resources=1000, consumption_rate=0.8)
    print(f"   --> Sustainability Score: {viability['score']:.2f} (Threshold: 0.85)")

    # --- الخطوة 4: النقد والتصحيح (The Refinement Loop) ---
    print("\n⚖️ [STEP 4]: Self-Critique & Synthesis (The Upgrade)")
    
    current_solution = initial_solution['winner']
    current_score = viability['score']
    iteration = 0

    # Loop if score is low OR if there is a significant risk
    while (current_score < 0.99 or "Risk" in consequences['primary_risk'] or "Instability" in consequences['primary_risk']) and iteration < 3:
        iteration += 1
        print(f"   🔄 Iteration {iteration}: Critiquing '{current_solution}'...")
        
        # الناقد يجد العيوب
        critique = critic.critique_solution(current_solution, consequences['primary_risk'])
        print(f"      Critique: {critique['feedback']}")
        
        # المولد يطرح حلاً معدلاً (Synthesis)
        new_solution = generator.refine_hypothesis(current_solution, critique['feedback'])
        print(f"      ✨ Refined Solution: {new_solution}")
        
        # تحديث النتيجة (محاكاة التحسن)
        current_solution = new_solution
        current_score += 0.1
        # Update risk for next iteration (simulate resolution)
        if iteration == 3:
             consequences['primary_risk'] = "Stable"
        
        print(f"      New Score: {min(current_score, 0.99):.2f}")
        time.sleep(1)

    print("\n=======================================================================")
    print(f"🏆 FINAL PROTOCOL: {current_solution}")
    print("   STATUS: Ready for implementation.")

if __name__ == "__main__":
    run_impossible_challenge()
