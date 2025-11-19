import unittest
from Integration_Layer.Intent_Recognizer import recognize_intent
from AGL_UI.Language_Interface import parse_entities
from Integration_Layer.Action_Router import route


class TestDialogueLayer(unittest.TestCase):
    def test_ohm_predict_I(self):
        txt = "احسب التيار وفق قانون اوم V=50 و R=10"
        intent = recognize_intent(txt)
        kv = parse_entities(txt)
        out = route(intent["task"], intent["law"], kv)
        self.assertTrue(out["ok"])
        self.assertIn("I", out["result"])

    def test_ohm_predict_R(self):
        txt = "احسب المقاومة: V=12 I=2"
        intent = recognize_intent(txt)
        kv = parse_entities(txt)
        out = route(intent["task"], intent["law"], kv)
        self.assertTrue(out["ok"])
        # result should contain R
        self.assertIn("R", out["result"])

    def test_ohm_predict_V_with_arabic_indic(self):
        # Uses Arabic-Indic digits for ٣ و ٤ (3 and 4)
        txt = "احسب الجهد عندما I=٣ و R=٤"
        intent = recognize_intent(txt)
        kv = parse_entities(txt)
        out = route(intent["task"], intent["law"], kv)
        self.assertTrue(out["ok"])
        self.assertIn("V", out["result"])


if __name__ == "__main__":
    unittest.main()
