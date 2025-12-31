import sys
import os

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def run_self_discovery():
    print("\n🔭 STARTING SELF-DISCOVERY AUDIT...")
    print("   Asking the system to find dormant capabilities within itself.")
    
    # Initialize the Awakened Mind
    asi = AGL_Super_Intelligence()
    
    # The "Self-Audit" Query
    # We ask it to look for specific high-value keywords in its map that are NOT in its active list.
    query = """
    Analyze your System Map (Self-Awareness Data). 
    Compare it with your 'Currently Active Components'.
    Identify 3-5 advanced engines or capabilities that exist in your code (System Map) but are NOT currently active.
    Look for keywords like 'Evolution', 'Simulation', 'Physics', 'Causal', 'Telepathy', or 'Resurrection'.
    List them and briefly explain what they might do based on their names.
    """
    
    print(f"\n❓ AUDIT QUERY: {query.strip()}")
    print("-" * 50)
    
    # Process
    response = asi.process_query(query)
    
    print("-" * 50)
    print(f"💡 DISCOVERY REPORT:\n{response}")
    print("-" * 50)

if __name__ == "__main__":
    run_self_discovery()
