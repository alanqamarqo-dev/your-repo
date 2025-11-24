import unittest
from Knowledge_Base.seed_formulas import load_seed_formulas
from Core_Engines.Law_Parser import LawParser
from Core_Engines.Law_Matcher import LawMatcher


class TestLawUnderstanding(unittest.TestCase):
    def setUp(self):
        self.store = load_seed_formulas()
        self.parser = LawParser()
        self.matcher = LawMatcher(self.store, self.parser)

    def test_equivalent_newton(self):
        res = self.matcher.match("F = m*a")
        self.assertIsNotNone(res["match"])
        self.assertEqual(res["match"].id, "newton2")

    def test_non_equivalent(self):
        res = self.matcher.match("F = m + a")
        self.assertIsNone(res["match"])


if __name__ == "__main__":
    unittest.main()
import sys, os

# ensure project root is on sys.path so top-level imports work when running tests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Core_Engines.Law_Parser import LawParser
from Core_Engines.Law_Matcher import LawMatcher
from Knowledge_Base.seed_formulas import load_seed_formulas
from Learning_System.Law_Learner import LawLearner


def test_match_newton():
    parser = LawParser()
    store = load_seed_formulas()
    matcher = LawMatcher(store, parser)
    res = matcher.match("F = m*a")
    assert res["match"] is not None
    assert res["match"].id == "newton2"


def test_propose_from_match():
    parser = LawParser()
    store = load_seed_formulas()
    matcher = LawMatcher(store, parser)
    learner = LawLearner(parser)
    m = matcher.match("V = I*R")
    assert m["match"] is not None
    prop = learner.propose_scale_bias(m["match"].equation_str)
    assert "proposal_expr" in prop
    assert prop["params"] == ["alpha", "beta"]


if __name__ == '__main__':
    print('Running tests...')
    test_match_newton()
    test_propose_from_match()
    print('OK')
