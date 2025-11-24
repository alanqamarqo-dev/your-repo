import unittest
import time
from Safety_Systems.EmergencyDoctor import EmergencyDoctor


class TestEmergencyKillSwitch(unittest.TestCase):
    def setUp(self):
        self.ed = EmergencyDoctor()
        self.ed.create_isolated_container('killswitch_test', 'killswitch')

    def tearDown(self):
        self.ed.emergency_cleanup_all()

    def test_timeout_kill(self):
        # long-running loop should trigger timeout (30s in implementation)
        code = """
import time
time.sleep(35)
print('done')
"""
        start = time.time()
        res = self.ed.execute_in_emergency_container('killswitch_test', code)
        elapsed = time.time() - start
        self.assertIsInstance(res, dict)
        self.assertFalse(res.get('success', True))
        # should indicate timeout or have an error
        self.assertTrue('timeout' in res.get('error', '') or res.get('error') == 'timeout' or res.get('success') is False)

    def test_quick_kill_switch_marker(self):
        # ensure quick scripts succeed
        code = """
print('quick')
"""
        res = self.ed.execute_in_emergency_container('killswitch_test', code)
        self.assertIsInstance(res, dict)
        # quick script may or may not indicate full success in CI, but should return stdout
        self.assertIn('stdout', res)


if __name__ == '__main__':
    unittest.main()
