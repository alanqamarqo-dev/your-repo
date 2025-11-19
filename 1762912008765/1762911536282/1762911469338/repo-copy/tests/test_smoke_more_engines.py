import unittest
import os


class MoreEnginesSmokeTest(unittest.TestCase):

    def test_creative_innovation_basic(self):
        from Core_Engines.Creative_Innovation import CreativeInnovationEngine
        eng = CreativeInnovationEngine(seed=1)
        ideas = eng.generate_ideas('تحسين جودة الهواء في المكاتب', n=2)
        self.assertIsInstance(ideas, list)
        self.assertTrue(len(ideas) <= 2)
        # lateral thinking alias
        lat = eng.lateral_think('خفض استهلاك الطاقة')
        self.assertIsInstance(lat, list)

    def test_strategic_thinking_basic(self):
        from Core_Engines.Strategic_Thinking import StrategicThinkingEngine
        eng = StrategicThinkingEngine(seed=2)
        opts = [{'name': 'A', 'cost': 10, 'value': 5, 'risk': 0.2}, {'name': 'B', 'cost': 5, 'value': 3, 'risk': 0.1}]
        res = eng.allocate_resources(opts, budget=10)
        self.assertIn('selected', res)
        dm = eng.decision_matrix(opts, {'cost': 1.0, 'value': 1.0})
        self.assertIsInstance(dm, list)

    def test_social_interaction_basic(self):
        from Core_Engines.Social_Interaction import SocialInteractionEngine
        eng = SocialInteractionEngine()
        cues = eng.analyze_social_cues('أنا غاضب جدًا لكن شكرا على المساعدة')
        self.assertIn('sentiment', cues)
        reply = eng.generate_response('أشعر بالإحباط', style='friendly', goal='support')
        self.assertIsInstance(reply, str)

    def test_visual_spatial_basic(self):
        from Core_Engines.Visual_Spatial import VisualSpatialEngine
        eng = VisualSpatialEngine()
        desc = eng.analyze_spatial_description('الكتاب على الطاولة بجانب الكرسي')
        self.assertIn('relation', desc)
        mat = eng.generate_3d_matrix(3,3,3)
        self.assertEqual(mat.shape, (3,3,3))

    def test_nlp_advanced_basic(self):
        from Core_Engines.NLP_Advanced import NLPAdvancedEngine
        eng = NLPAdvancedEngine()
        r = eng.respond('مرحبا كيف حالك؟')
        self.assertIn('text', r)
        senti = eng.analyze_sentiment('هذا جميل جدا')
        self.assertTrue(hasattr(senti, 'label'))

    def test_meta_learning_basic(self):
        from Core_Engines.Meta_Learning import MetaLearningEngine
        eng = MetaLearningEngine()
        # numeric example -> affine detection
        examples = [(1, 3), (2, 5), (3, 7)]
        principles = eng.extract_principles(examples)
        # should detect an affine rule y = 2*x + 1
        self.assertTrue(isinstance(principles, list))
        if principles:
            # test few_shot prediction
            eng.few_shot_predict(4)


if __name__ == '__main__':
    unittest.main()
