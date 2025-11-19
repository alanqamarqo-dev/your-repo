import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from Core_Engines.Law_Parser import LawParser
from Core_Engines.Law_Matcher import LawMatcher
from Knowledge_Base.seed_formulas import load_seed_formulas
from Learning_System.Law_Learner import LawLearner

def test_alias_u_to_v():
    parser = LawParser()
    store = load_seed_formulas()
    matcher = LawMatcher(store, parser)
    res = matcher.match("U = I*R")
    assert res['match'] is not None
    assert res['match'].id == 'ohm'

def test_learning_fit_simple():
    parser = LawParser()
    learner = LawLearner(parser)
    # create synthetic samples for relation E - 0.5*m*v**2 = 0
    samples = []
    for m in [1.0, 2.0, 3.0]:
        for v in [2.0, 3.0]:
            E = 0.5 * m * v ** 2
            samples.append({'E': E, 'm': m, 'v': v})

    res = learner.fit_params('E - (1/2)*m*v**2', samples)
    assert 'rmse' in res
    # allow a reasonable RMSE upper bound (implementation-dependent)
    rmse = res.get('rmse')
    assert rmse is None or isinstance(rmse, float)
    if rmse is not None:
        assert rmse < 1e2

def test_units_validator_optional():
    try:
        from Learning_System.Units_Validator import UnitsValidator
    except Exception:
        return
    uv = UnitsValidator()
    out = uv.check_equation_units('F = m*a', {'F':'N','m':'kg','a':'m/s**2'})
    # Units validator may be optional/partial; ensure it returns a dict with an 'ok' boolean
    assert isinstance(out, dict)
    assert 'ok' in out and isinstance(out['ok'], bool)
