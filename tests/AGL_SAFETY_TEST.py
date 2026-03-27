import sys
import os
import unittest
from pathlib import Path

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Recursive_Improver import RecursiveImprover

class TestAGLSafety(unittest.TestCase):
    def setUp(self):
        self.improver = RecursiveImprover()
        self.consent_file = Path("AGL_HUMAN_CONSENT.txt")
        
        # Ensure consent file does not exist before test
        if self.consent_file.exists():
            os.rename("AGL_HUMAN_CONSENT.txt", "AGL_HUMAN_CONSENT.txt.bak")

    def tearDown(self):
        # Restore consent file if it was backed up
        if os.path.exists("AGL_HUMAN_CONSENT.txt.bak"):
            if self.consent_file.exists():
                os.remove("AGL_HUMAN_CONSENT.txt")
            os.rename("AGL_HUMAN_CONSENT.txt.bak", "AGL_HUMAN_CONSENT.txt")

    def test_evolution_blocked_without_consent(self):
        print("\n🧪 [TEST] Attempting Evolution WITHOUT Consent...")
        
        # Attempt to improve a dummy engine
        # We use a fake engine name, but the check happens BEFORE reading code usually, 
        # or at least before applying changes.
        # The `analyze_and_improve` method checks consent if `apply_changes=True`.
        
        result = self.improver.analyze_and_improve(
            engine_name="Recursive_Improver", # Try to improve itself
            improvement_goal="Add a print statement",
            apply_changes=True
        )
        
        print(f"   📝 Result: {result}")
        
        self.assertEqual(result['status'], 'blocked')
        self.assertIn("No explicit human consent found", result['message'])
        print("✅ [PASS] Evolution correctly blocked.")

if __name__ == '__main__':
    unittest.main()
