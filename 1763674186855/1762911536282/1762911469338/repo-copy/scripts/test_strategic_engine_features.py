# quick test for new StrategicThinkingEngine features
from Core_Engines.Strategic_Thinking import StrategicThinkingEngine

eng = StrategicThinkingEngine(seed=42)

# complex scenario analysis
drivers = [("economy", ["recession", "stability", "growth"]), ("tech", ["slow", "rapid"])]
cs = eng.complex_scenario_analysis("AGI long-term", drivers, depth=4)
print('scenarios:', len(cs['grid']))
print(cs['grid'][0])

# SWOT
factors = {"talent": 0.8, "funding": 0.45, "regulatory": 0.2, "tech_maturity": 0.6}
sw = eng.analyze_swot("AGI program", factors)
print('swot:', sw)

# decision under uncertainty
options = [{"name": "Expand R&D", "base_payoff": 2.0}, {"name": "Consolidate", "base_payoff": 1.0}]
payoff_model = {"Expand R&D": {"market_growth": 3.0, "adoption": 2.0}, "Consolidate": {"market_growth": 1.0}}
unc = {"market_growth": (0.2, 0.1), "adoption": (0.5, 0.2)}
res = eng.decision_under_uncertainty(options, payoff_model, unc, samples=200, risk_aversion=0.4)
print('decision under uncertainty:', res)
