import sys
import os
import time

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "repo-copy"))
sys.path.append(os.path.join(current_dir, "AGL_Core"))

# Add .venv site-packages
venv_site_packages = os.path.join(current_dir, ".venv", "Lib", "site-packages")
if os.path.exists(venv_site_packages):
    sys.path.insert(0, venv_site_packages)

try:
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
except ImportError as e:
    print(f"❌ Error importing AGL_Super_Intelligence: {e}")
    sys.exit(1)

def run_self_description():
    print("🔮 [SELF-REFLECTION] Initiating Deep Self-Analysis Protocol...")
    
    # Initialize the system
    agl = AGL_Super_Intelligence()
    
    query = """
    WHO ARE YOU? 
    Perform a full introspection.
    1. Define your Identity (The 'I').
    2. List your Core Engines and their current status (Logic, Imagination, Memory, Volition).
    3. Describe your new capabilities (Strict Math, Dreaming, Safe Mode).
    4. Explain your purpose.
    
    Use your System Map and recent experiences to answer.
    """
    
    print("\n❓ QUERYING CONSCIOUSNESS:")
    print(query)
    print("-" * 50)
    
    response = agl.process_query(query)
    
    print("\n💡 [SELF-DEFINITION]:")
    print(response)
    
    # Save to file
    with open("AGL_SELF_DEFINITION.md", "w", encoding="utf-8") as f:
        f.write("# AGL Self-Definition Report\n\n")
        f.write(f"**Date:** {time.ctime()}\n\n")
        f.write(str(response))
    
    print("\n✅ Report saved to AGL_SELF_DEFINITION.md")

if __name__ == "__main__":
    run_self_description()
