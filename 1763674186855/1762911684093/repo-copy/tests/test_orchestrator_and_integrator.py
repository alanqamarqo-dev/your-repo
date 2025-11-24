import unittest, tempfile, os, json
from Integration_Layer.Task_Orchestrator import TaskOrchestrator
from Learning_System.Knowledge_Integrator import KnowledgeIntegrator


class TestOrchestratorAndIntegrator(unittest.TestCase):
    def test_law_validate_missing_subsystem(self):
        orch = TaskOrchestrator()
        # Provide a formula but orchestrator may have law subsystem uninitialized in test environments
        res = orch.process('law_validate', formula='F = k * x')
        self.assertIn('status', res) # type: ignore

    def test_knowledge_integrator_updates_cfg_and_logs(self):
        td = tempfile.TemporaryDirectory()
        ki = KnowledgeIntegrator(base_dir=td.name)
        # update config
        plan = {'fusion_weights': {'mathematical_brain': 1.2}, 'confidence_gate': {'min_pass': 0.6}}
        r = ki.integrate_new_knowledge(plan)
        self.assertEqual(r.get('action'), 'config_updated')
        # append a run record
        run = {'task': 'test', 'result': {'ok': True}}
        r2 = ki.integrate_new_knowledge(run)
        self.assertEqual(r2.get('action'), 'experience_logged')
        # file should exist
        self.assertTrue(os.path.exists(os.path.join(td.name, 'data', 'experiences.jsonl')))
        td.cleanup()


if __name__ == '__main__':
    unittest.main()
