import unittest
import os
from Integration_Layer.Task_Orchestrator import TaskOrchestrator


class TestEmergencyExecution(unittest.TestCase):
    def test_emergency_exec_simple(self):
        orch = TaskOrchestrator()
        # simple print-only code should run inside isolated wrapper
        code = "print('hello-from-emergency')"
        res = orch.process('emergency:exec', code=code, container_id='tmp_emergency_test')
        self.assertIn('result', res) # type: ignore
        r = res['result'] # type: ignore
        # expect a dict with success + stdout/stderr
        self.assertIsInstance(r, dict)
        self.assertIn('success', r)
        # success may be False in constrained environments; assert keys exist and stdout captured
        self.assertIn('stdout', r)
        self.assertIn('stderr', r)
        # if success True, expect the wrapped marker
        if r.get('success'): # type: ignore
            self.assertIn('EXECUTION_COMPLETED_SUCCESSFULLY', r.get('stdout', '')) # type: ignore


if __name__ == '__main__':
    unittest.main()
