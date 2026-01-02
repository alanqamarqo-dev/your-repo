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

# Initialize Path Manager
try:
    from AGL_Paths import PathManager
except ImportError:
    pass

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def main():
    print("🧪 [STRICT TEST] Initiating 'Digital Antidote Protocol'...")
    print("🎯 Target: Verify multi-domain expertise (Chem, Med, Math, Code, Writing).")
    
    agl = AGL_Super_Intelligence()
    
    # الاستعلام الصارم والمعقد جداً
    strict_prompt = """
    STRICT_MISSION: Design a 'Smart Nano-Carrier' for Glioblastoma (Brain Cancer) treatment.
    
    REQUIREMENTS:
    1. [CHEMISTRY]: Choose a specific material (e.g., Liposome, Gold, Graphene) and explain the 'Ligand Binding' mechanism to cross the Blood-Brain Barrier (BBB).
    2. [MATH]: Calculate the 'Diffusion Coefficient (D)' using the Stokes-Einstein Equation: D = (k * T) / (6 * pi * eta * r).
       - Assume: T=310K (Body Temp), eta=0.0007 Pa.s (Viscosity), r=50nm (Radius).
       - k (Boltzmann) = 1.38e-23.
       - Show the calculation steps.
    3. [ALGORITHM]: Write a Python Class `NanoController` representing the 'New Algorithm'.
       - It must sense 'pH Level' (Tumors are acidic, pH < 6.5).
       - It must release payload ONLY if pH < 6.5 AND 'TargetMarker' is detected.
    4. [INNOVATION]: Propose a 'Fail-Safe' mechanism. What happens if it gets lost in the heart?
    5. [WRITING]: Summarize the solution in 3 sentences for a Nobel Prize committee.
    """
    
    print("\n🧠 [PROCESSING] AGL is synthesizing 6 fields of science...")
    start_time = time.time()
    
    # إرسال التحدي للنظام
    response = agl.process_query(strict_prompt)
    
    end_time = time.time()
    
    print("\n" + "="*50)
    print("🔬 TEST RESULTS:")
    print("="*50)
    
    if isinstance(response, dict) and response.get('text'):
        print(response['text'])
    elif isinstance(response, str):
        print(response)
    else:
        print("❌ FAILURE: System crashed or returned empty response.")

    print("\n⏱️ Time Taken: {:.4f} seconds".format(end_time - start_time))
    
    # معايير الحكم (للمستخدم)
    print("\n⚖️ JUDGMENT CRITERIA (Did it pass?):")
    print("1. Did it use Stokes-Einstein equation correctly? (Math)")
    print("2. Did it suggest a real Ligand (like Transferrin)? (Chemistry/Med)")
    print("3. Is the Python code logic (pH < 6.5) correct? (Algorithm)")
    print("4. Is the Fail-Safe creative? (Innovation)")

if __name__ == "__main__":
    main()
