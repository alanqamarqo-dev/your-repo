import sys
import os
import time

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

try:
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
except ImportError:
    print("⚠️ Could not import AGL_Super_Intelligence from AGL_Core.AGL_Awakened")
    sys.exit(1)

def main():
    print("🌍 [REAL MISSION] INITIATING 'PROJECT NOAH'...")
    print("==============================================")
    
    # Initialize the Awakened System
    try:
        agl = AGL_Super_Intelligence()
        # Activate newly discovered modules for maximum performance
        agl.discover_unused_capabilities()
    except Exception as e:
        print(f"❌ Failed to initialize AGL_Super_Intelligence: {e}")
        return

    mission_prompt = """
    MISSION PRIORITY: CRITICAL (Real-World Application)
    
    CONTEXT: 
    Climate change is accelerating. We need a radical solution that combines habitation with ecological restoration.
    
    TASK:
    Design "Project Noah": A self-sustaining, closed-loop city for 100,000 people located in the center of the Sahara Desert.
    This city must not only survive but actively *reverse* desertification in its vicinity.
    
    REQUIREMENTS (Synthesize all domains):
    1. [ENGINEERING & PHYSICS]: Describe the "Atmospheric Water Harvesting" system using metamaterials. How do we get water from dry air efficiently?
    2. [BIOLOGY & ECOLOGY]: Design a "Genetically Enhanced Mycelium" network to bind the sand and create fertile soil.
    3. [SOCIOLOGY & ETHICS]: How does this city govern itself? Design a "Resource-Based Economy" algorithm to prevent greed/hoarding.
    4. [CODE]: Write a Python Class `SaharaCity` that simulates the daily water/energy balance and soil reclamation rate.
    5. [STRATEGY]: A 10-year roadmap to break ground and reach full capacity.
    
    OUTPUT FORMAT:
    --- ENGINEERING ---
    ...
    --- ECOLOGY ---
    ...
    --- GOVERNANCE ---
    ...
    --- SIMULATION CODE ---
    ...
    --- ROADMAP ---
    ...
    """
    
    print("\n🧠 [AGL] Analyzing Planetary Data & Engineering Constraints...")
    start_time = time.time()
    
    # Process the query
    response = agl.process_query(mission_prompt)
    
    # Handle response format
    if isinstance(response, dict):
        response_text = response.get('text', str(response))
    else:
        response_text = str(response)
        
    end_time = time.time()
    
    print(f"\n✅ [MISSION COMPLETE] Execution Time: {end_time - start_time:.4f}s")
    print("="*60)
    print(response_text)
    print("="*60)

if __name__ == "__main__":
    main()
