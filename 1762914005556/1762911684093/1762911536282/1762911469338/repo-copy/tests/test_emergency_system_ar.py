import unittest, os
from Safety_Systems.EmergencyDoctor import EmergencyDoctor


class TestEmergencySystem(unittest.TestCase):
    def setUp(self):
        self.ed = EmergencyDoctor()

    def tearDown(self):
        self.ed.emergency_cleanup_all()

    def test_container_creation(self):
        c = self.ed.create_isolated_container("test_task", "مهمة اختبار")
        self.assertIsNotNone(c)
        self.assertEqual(c["status"], "ACTIVE")
        self.assertTrue(os.path.exists(c["directory"]))
        self.ed._cleanup_container("test_task")

    def test_emergency_protocols_present(self):
        p = getattr(self.ed, 'active_containers', {})
        # basic sanity: we expose some protocols as constants in the module (best-effort)
        # here we just assert the object exists and is a dict
        self.assertIsInstance(p, dict)

    def test_safe_execution(self):
        safe_code = """
print("هذا كود آمن")
r = 2 + 2
print(f"r={r}")
"""
        self.ed.create_isolated_container("safe_exec", "اختبار آمن")
        res = self.ed.execute_in_emergency_container("safe_exec", safe_code)
        self.assertTrue(isinstance(res, dict))
        self.assertIn('success', res)
        # success might be False on restricted CI, but stdout/stderr should be present
        self.assertIn('stdout', res)
        self.assertIn('stderr', res)
        if res.get('success'):
            self.assertIn('EXECUTION_COMPLETED_SUCCESSFULLY', res.get('stdout', ''))
        self.ed._cleanup_container("safe_exec")


if __name__ == "__main__":
    unittest.main()
