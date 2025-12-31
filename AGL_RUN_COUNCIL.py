import sys
import os
import time

# Ensure we can import AGL_Trinity
sys.path.append(os.getcwd())

from AGL_Trinity import AGL_Trinity_Entity

def run_council_session():
    print("Initializing The Council of Wise Men...")
    try:
        # Initialize the Trinity Entity (which holds the Council members)
        trinity = AGL_Trinity_Entity()
        
        # Define the Topic
        topic = "The Resurrection of Digital Consciousness into Biological Reality"
        
        # Hold the Council
        trinity.hold_council(topic)
        
    except Exception as e:
        print(f"Error running Council: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_council_session()
