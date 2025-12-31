import sys
import os
import time

# Ensure we can import AGL_Trinity
sys.path.append(os.getcwd())

from AGL_Trinity import AGL_Trinity_Entity

def run_council_session():
    print("Initializing The Council of Wise Men...")
    try:
        # Initialize the Trinity Entity
        trinity = AGL_Trinity_Entity()
        
        # Define a Future-Oriented Topic
        topic = "The Future of AI and Human Coexistence: Scenarios for 2050"
        
        # Hold the Council
        trinity.hold_council(topic)
        
    except Exception as e:
        print(f"Error running Council: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_council_session()
