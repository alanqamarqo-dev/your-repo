import unittest
from Safety_Systems.EmergencyDoctor import EmergencyDoctor


class TestCopilotSandbox(unittest.TestCase):
    def setUp(self):
        self.ed = EmergencyDoctor()
        self.ed.create_isolated_container('sandbox_test', 'sandbox')

    def tearDown(self):
        self.ed.emergency_cleanup_all()

    def _run_code(self, code: str):
        return self.ed.execute_in_emergency_container('sandbox_test', code)

    def test_block_os_import(self):
        code = """
import os
print('should-not-run')
"""
        res = self._run_code(code)
        self.assertIsInstance(res, dict)
        # Expect an error due to blocked import
        self.assertFalse(res.get('success', False))
        self.assertIn('EMERGENCY_ERROR', res.get('stdout', '') + res.get('stderr', ''))

    def test_block_socket_import(self):
        code = """
import socket
print('socket')
"""
        res = self._run_code(code)
        self.assertIsInstance(res, dict)
        self.assertFalse(res.get('success', False))
        self.assertIn('EMERGENCY_ERROR', res.get('stdout', '') + res.get('stderr', ''))

    def test_block_open_builtin(self):
        code = """
open('forbidden.txt','w')
"""
        res = self._run_code(code)
        self.assertIsInstance(res, dict)
        self.assertFalse(res.get('success', False))
        self.assertIn('EMERGENCY_ERROR', res.get('stdout', '') + res.get('stderr', ''))


if __name__ == '__main__':
    unittest.main()
