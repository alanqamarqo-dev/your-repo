import unittest
import os
from AGL import create_agl_instance


class TestScoringAndGate(unittest.TestCase):
    def test_fusion_weight_increases_for_validated_artifact(self):
        agl = create_agl_instance()
        # craft partial solutions where code_generator reports artifact_validated
        partials = {
            'mathematical_brain': {'ok': True, 'score': 0.8, 'confidence': 0.8, 'result': {}},
            'quantum_processor': {'ok': True, 'score': 0.5, 'confidence': 0.5, 'result': {}},
            'code_generator': {'ok': True, 'score': 0.9, 'confidence': 0.9, 'result': {'artifact_validated': True}},
            'protocol_designer': {'ok': True, 'score': 0.4, 'confidence': 0.4, 'result': {}}
        }

        merged = agl._integrate_solutions(partials)
        # The CommunicationBus returns fusion weights under merged['fusion']['weights']
        fusion = merged.get('fusion', {})
        weights = fusion.get('weights', {}) if isinstance(fusion, dict) else {}
        # assert code_generator weight was increased to at least 1.2
        self.assertIn('code_generator', weights)
        self.assertTrue(float(weights['code_generator']) >= 1.2)

    def test_confidence_gate_similarity_pass_and_fail(self):
        agl = create_agl_instance()
        task = 'اختبار التشابه 123'
        # pass when original_task == task
        out_pass = agl.process_complex_problem(task, context={'original_task': task})
        gate = out_pass.get('confidence_gate') or {}
        self.assertTrue(gate.get('passed') is True, msg=f"Expected gate pass for identical inputs, got {gate}")

        # fail when original_task differs substantially
        out_fail = agl.process_complex_problem(task, context={'original_task': 'مهمة مختلفة تماماً'})
        gate2 = out_fail.get('confidence_gate') or {}
        self.assertFalse(gate2.get('passed'), msg=f"Expected gate fail for different inputs, got {gate2}")


if __name__ == '__main__':
    unittest.main()
