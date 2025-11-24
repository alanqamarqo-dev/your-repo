import unittest
import os


class SmokeEnginesTest(unittest.TestCase):

    def test_import_core_engines(self):
        # ensure package imports work
        import Core_Engines.General_Knowledge as gk
        import Core_Engines.External_InfoProvider as eip
        self.assertTrue(hasattr(gk, 'GeneralKnowledgeEngine'))
        self.assertTrue(hasattr(eip, 'ExternalInfoProvider'))

    def test_general_knowledge_mock(self):
        from Core_Engines.General_Knowledge import GeneralKnowledgeEngine
        # instantiate and call ask with empty context; should not raise
        g = GeneralKnowledgeEngine()
        res = g.ask('ما معنى الاختبار؟', context=['اختبار نموذجي'])
        self.assertIn('ok', res)

    def test_external_provider_mock(self):
        # set mock env var to avoid network
        os.environ['AGL_EXTERNAL_INFO_MOCK'] = '1'
        from Core_Engines.External_InfoProvider import ExternalInfoProvider
        prov = ExternalInfoProvider()
        r = prov.fetch_facts('ما هي أسباب ازدحام المرور؟', hints=['domain:transport'])
        self.assertTrue(r.get('ok'))
        self.assertTrue(isinstance(r.get('facts', []), list))


if __name__ == '__main__':
    unittest.main()
