import unittest
import sys
import os
import time
import shutil

# Add repo-copy to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'repo-copy'))

from Learning_System.ExperienceMemory import ExperienceMemory

class TestGravitationalMemory(unittest.TestCase):
    def setUp(self):
        self.test_db = "tests_hilt/test_memory.jsonl"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.memory = ExperienceMemory(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_memory_attraction(self):
        """Test if important memories (high mass) are retrieved first."""
        current_time = time.time()
        
        # 1. Important Old Memory (Massive)
        self.memory.append({
            "id": "relativity",
            "content": "E=mc^2",
            "importance": 100.0,
            "intensity": 1.0,
            "timestamp": current_time - 10000 # Old
        })
        
        # 2. Trivial Recent Memory (Light)
        self.memory.append({
            "id": "cat_food",
            "content": "Buy cat food",
            "importance": 1.0,
            "intensity": 1.0,
            "timestamp": current_time - 10 # Recent
        })
        
        # Retrieve
        results = self.memory.retrieve_gravitational(top_k=2)
        top_result = results[0]
        
        print(f"Top Result: {top_result['id']}")
        self.assertEqual(top_result['id'], "relativity")

if __name__ == '__main__':
    unittest.main()
