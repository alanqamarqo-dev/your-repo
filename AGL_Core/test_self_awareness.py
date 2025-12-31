import sys
import os
import unittest

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

class TestSelfAwareness(unittest.TestCase):
    def test_system_map_loading(self):
        print("\n🧪 Testing Self-Awareness Module Integration...")
        # Suppress stdout for the initialization noise if needed, but seeing it is good for verification
        asi = AGL_Super_Intelligence()
        
        self.assertIsNotNone(asi.self_awareness, "SelfAwarenessModule should be instantiated")
        self.assertIsNotNone(asi.self_awareness.system_map, "System Map should be loaded")
        self.assertGreater(len(asi.self_awareness.system_map), 0, "System Map should not be empty")
        
        print("✅ Self-Awareness Module loaded successfully.")
        print(f"   Map Size: {len(asi.self_awareness.system_map)} chars")
        
        # Check if a known file exists in the map
        self.assertIn("AGL_Awakened.py", asi.self_awareness.system_map, "AGL_Awakened.py should be in the map")

if __name__ == '__main__':
    unittest.main()
