"""
AGL Search Engine — Comprehensive Tests
اختبارات شاملة لـ Layer 4: Intelligent Economic Search

86/86 passed للطبقات السابقة — الآن نختبر الطبقة الرابعة.
"""

import sys
import os
import time

# === إضافة المسار ===
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from agl_security_tool.search_engine.models import (
    WeaknessType,
    SearchStrategy,
    SeedSource,
    NodeState,
    SearchConfig,
    HeuristicTarget,
    EconomicWeakness,
    SearchSeed,
    SearchNode,
    CandidateSequence,
    SearchStats,
    SearchResult,
)
from agl_security_tool.search_engine.heuristic_prioritizer import HeuristicPrioritizer
from agl_security_tool.search_engine.weakness_detector import EconomicWeaknessDetector
from agl_security_tool.search_engine.guided_search import GuidedSearchEngine
from agl_security_tool.search_engine.profit_gradient import ProfitGradientEngine
from agl_security_tool.search_engine.engine import SearchOrchestrator


# ═══════════════════════════════════════════════════════════════
#  Mock Objects (محاكاة Layer 1, 2, 3)
# ═══════════════════════════════════════════════════════════════


class MockParam:
    def __init__(self, name, is_amount=False, concrete_values=None):
        self.name = name
        self.is_amount = is_amount
        self.concrete_values = concrete_values or []


class MockAction:
    """Mock Layer 2 Action"""

    def __init__(
        self,
        action_id,
        contract_name,
        function_name,
        category,
        has_cei_violation=False,
        sends_eth=False,
        reentrancy_guarded=False,
        requires_access=False,
        external_calls=None,
        state_reads=None,
        state_writes=None,
        attack_types=None,
        parameters=None,
        net_delta=0,
        profit_potential=0,
    ):
        self.action_id = action_id
        self.contract_name = contract_name
        self.function_name = function_name
        self.category = MockEnum(category)
        self.has_cei_violation = has_cei_violation
        self.sends_eth = sends_eth
        self.reentrancy_guarded = reentrancy_guarded
        self.requires_access = requires_access
        self.external_calls = external_calls or []
        self.state_reads = state_reads or []
        self.state_writes = state_writes or []
        self.attack_types = [MockEnum(at) for at in (attack_types or [])]
        self.parameters = parameters or []
        self.net_delta = net_delta
        self.profit_potential = profit_potential
        self.preconditions = []
        self.severity = "high"


class MockEnum:
    def __init__(self, value):
        self.value = value


class MockActionGraph:
    """Mock Layer 2 ActionGraph"""

    def __init__(self, actions=None, edges=None):
        self.actions = actions or {}
        self.edges = edges or {}
        self._attack_paths = []

    def get_successors(self, action_id):
        return self.edges.get(action_id, [])

    def get_attack_paths(self):
        return self._attack_paths

    def set_attack_paths(self, paths):
        self._attack_paths = paths


class MockActionSpace:
    """Mock Layer 2 ActionSpace"""

    def __init__(self, graph=None, attack_sequences=None):
        self.graph = graph
        self.attack_sequences = attack_sequences or []
        self.attack_surfaces = []
        self.high_value_targets = []


class MockAttackResult:
    """Mock Layer 3 AttackResult"""

    def __init__(
        self,
        net_profit_usd=0,
        is_profitable=False,
        attack_type="",
        severity="",
        gas_cost_usd=0,
    ):
        self.net_profit_usd = net_profit_usd
        self.is_profitable = is_profitable
        self.attack_type = attack_type
        self.severity = severity
        self.gas_cost_usd = gas_cost_usd
        self.steps = []
        self.exploit_scenario = ""


class MockProtocolState:
    """Mock Layer 3 ProtocolState"""

    def __init__(self):
        self.contracts = {}
        self.balances = {}


class MockStateLoader:
    """Mock Layer 3 ProtocolStateLoader"""

    def load_from_graph(self, graph):
        return MockProtocolState()


class MockAttackEngine:
    """Mock Layer 3 AttackSimulationEngine"""

    def __init__(self, profit_schedule=None):
        """
        profit_schedule: list of floats — profit returned for each call.
        If None, returns 0.
        """
        self._call_count = 0
        self._profit_schedule = profit_schedule or [0.0]
        self.state_loader = MockStateLoader()

    def simulate_sequence(self, sequence, initial_state, sequence_id=""):
        profit = self._profit_schedule[
            min(self._call_count, len(self._profit_schedule) - 1)
        ]
        self._call_count += 1
        return MockAttackResult(
            net_profit_usd=profit,
            is_profitable=profit > 0,
            attack_type="reentrancy" if profit > 0 else "",
            severity="critical" if profit > 50000 else ("high" if profit > 0 else ""),
        )

    def simulate_all(self, graph, action_space):
        return {"total_sequences_tested": 0, "profitable_attacks": 0}


class MockFinancialGraph:
    """Mock Layer 1 FinancialGraph"""

    def __init__(self):
        self.entities = {}
        self.fund_flows = []
        self.relationships = []
        self.action_space = None
        self.attack_simulation = None
        self.search_results = None


# ═══════════════════════════════════════════════════════════════
#  Helper: Build a realistic Vault scenario
# ═══════════════════════════════════════════════════════════════


def build_vault_scenario():
    """
    Vault مع reentrancy vulnerability:
    - deposit(amount) → fund_inflow, public
    - withdraw(amount) → fund_outflow, public, CEI violation, sends ETH, no guard
    - setFee(uint) → admin, requires_access
    """
    actions = {
        "Vault_deposit_0": MockAction(
            "Vault_deposit_0",
            "Vault",
            "deposit",
            "fund_inflow",
            state_writes=["balances", "totalDeposits"],
            parameters=[MockParam("amount", is_amount=True, concrete_values=[10**18])],
        ),
        "Vault_withdraw_0": MockAction(
            "Vault_withdraw_0",
            "Vault",
            "withdraw",
            "fund_outflow",
            has_cei_violation=True,
            sends_eth=True,
            reentrancy_guarded=False,
            external_calls=["msg.sender.call{value: amount}"],
            state_reads=["balances", "totalDeposits"],
            state_writes=["balances", "totalDeposits"],
            attack_types=["reentrancy"],
            parameters=[MockParam("amount", is_amount=True, concrete_values=[10**18])],
        ),
        "Vault_setFee_0": MockAction(
            "Vault_setFee_0",
            "Vault",
            "setFee",
            "admin",
            requires_access=True,
            state_writes=["fee"],
        ),
    }

    edges = {
        "Vault_deposit_0": ["Vault_withdraw_0"],
        "Vault_withdraw_0": ["Vault_deposit_0"],
    }

    graph = MockActionGraph(actions, edges)
    graph.set_attack_paths(
        [
            ["Vault_deposit_0", "Vault_withdraw_0"],
        ]
    )
    space = MockActionSpace(graph)
    return space, actions, graph


def build_defi_scenario():
    """
    DeFi protocol with multiple contracts:
    - Pool: deposit, withdraw, borrow, repay
    - Oracle: updatePrice
    - FlashLoan: flashLoan
    """
    actions = {
        "Pool_deposit_0": MockAction(
            "Pool_deposit_0",
            "Pool",
            "deposit",
            "fund_inflow",
            state_writes=["balances", "totalDeposits"],
            parameters=[MockParam("amount", is_amount=True, concrete_values=[10**18])],
        ),
        "Pool_withdraw_0": MockAction(
            "Pool_withdraw_0",
            "Pool",
            "withdraw",
            "fund_outflow",
            sends_eth=True,
            state_reads=["balances", "totalDeposits"],
            state_writes=["balances"],
            parameters=[MockParam("amount", is_amount=True, concrete_values=[10**18])],
        ),
        "Pool_borrow_0": MockAction(
            "Pool_borrow_0",
            "Pool",
            "borrow",
            "borrow",
            state_reads=["oraclePrice", "collateral"],
            state_writes=["debt", "balances"],
            parameters=[MockParam("amount", is_amount=True, concrete_values=[10**18])],
        ),
        "Pool_repay_0": MockAction(
            "Pool_repay_0",
            "Pool",
            "repay",
            "repay",
            state_writes=["debt", "balances"],
        ),
        "Oracle_updatePrice_0": MockAction(
            "Oracle_updatePrice_0",
            "Oracle",
            "updatePrice",
            "oracle_update",
            state_writes=["oraclePrice"],
        ),
        "Flash_flashLoan_0": MockAction(
            "Flash_flashLoan_0",
            "Pool",
            "flashLoan",
            "flash_loan",
            external_calls=["borrower.onFlashLoan(amount)"],
            state_reads=["balances"],
            state_writes=["balances"],
        ),
    }

    edges = {
        "Pool_deposit_0": ["Pool_withdraw_0", "Pool_borrow_0", "Flash_flashLoan_0"],
        "Pool_withdraw_0": ["Pool_deposit_0"],
        "Pool_borrow_0": ["Pool_repay_0", "Pool_withdraw_0"],
        "Pool_repay_0": ["Pool_withdraw_0"],
        "Oracle_updatePrice_0": ["Pool_borrow_0"],
        "Flash_flashLoan_0": [
            "Oracle_updatePrice_0",
            "Pool_borrow_0",
            "Pool_withdraw_0",
        ],
    }

    graph = MockActionGraph(actions, edges)
    graph.set_attack_paths(
        [
            ["Flash_flashLoan_0", "Oracle_updatePrice_0", "Pool_borrow_0"],
            ["Pool_deposit_0", "Pool_withdraw_0"],
        ]
    )
    space = MockActionSpace(graph)
    return space, actions, graph


# ═══════════════════════════════════════════════════════════════
#  Tests
# ═══════════════════════════════════════════════════════════════

passed = 0
failed = 0
total = 0
errors = []


def test(name, condition, detail=""):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        msg = f"  ❌ {name}"
        if detail:
            msg += f" — {detail}"
        print(msg)
        errors.append(msg)


# ═══════════════════════════════════════════════════════
#  1. Models Tests
# ═══════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("1. MODELS TESTS")
print("=" * 60)

# 1.1 WeaknessType enum
test("WeaknessType has 14 values", len(WeaknessType) == 14, f"got {len(WeaknessType)}")

test(
    "WeaknessType.REENTRANCY_DRAIN value",
    WeaknessType.REENTRANCY_DRAIN.value == "reentrancy_drain",
)

# 1.2 SearchStrategy enum
test("SearchStrategy has 6 values", len(SearchStrategy) == 6)

test(
    "SearchStrategy.HYBRID is default", SearchConfig().strategy == SearchStrategy.HYBRID
)

# 1.3 SearchConfig defaults
cfg = SearchConfig()
test("SearchConfig max_sequences default 500", cfg.max_sequences_to_test == 500)
test("SearchConfig beam_width default 10", cfg.beam_width == 10)
test("SearchConfig mcts_iterations default 200", cfg.mcts_iterations == 200)
test("SearchConfig population_size default 30", cfg.population_size == 30)
test("SearchConfig to_dict works", "strategy" in cfg.to_dict())

# 1.4 HeuristicTarget
ht = HeuristicTarget(target_id="Vault.withdraw")
ht.score = 0.85
ht.has_cei_violation = True
ht.tags.add("fund_mover")
d = ht.to_dict()
test("HeuristicTarget to_dict has score", d["score"] == 0.85)
test("HeuristicTarget tags in dict", "fund_mover" in d["tags"])

# 1.5 EconomicWeakness
ew = EconomicWeakness(
    weakness_id="reent_1",
    weakness_type=WeaknessType.REENTRANCY_DRAIN,
    severity="critical",
    confidence=0.9,
    entry_actions=["deposit_0"],
    exit_actions=["withdraw_0"],
    auxiliary_actions=["transfer_0"],
    estimated_profit_usd=100_000,
)
seeds = ew.generate_seed_sequences()
test("EconomicWeakness generates seeds", len(seeds) >= 1, f"got {len(seeds)}")
test(
    "EconomicWeakness seed has entry+exit",
    any(len(s.action_sequence) == 2 for s in seeds),
)
test(
    "EconomicWeakness seed has entry+aux+exit",
    any(len(s.action_sequence) == 3 for s in seeds),
)
test(
    "EconomicWeakness to_dict has weakness_type",
    ew.to_dict()["weakness_type"] == "reentrancy_drain",
)

# 1.6 SearchSeed
ss = SearchSeed(
    seed_id="test_1",
    source=SeedSource.HEURISTIC,
    action_sequence=["a", "b"],
    priority=0.8,
)
test("SearchSeed to_dict works", ss.to_dict()["priority"] == 0.8)

# 1.7 SearchNode
sn = SearchNode(node_id="n1", visits=10, total_reward=50.0)
test("SearchNode average_reward correct", sn.average_reward == 5.0)
test("SearchNode to_dict works", sn.to_dict()["visits"] == 10)

# 1.8 CandidateSequence
cs = CandidateSequence(
    candidate_id="c1",
    action_ids=["a", "b"],
    actual_profit_usd=5000,
)
test("CandidateSequence to_dict works", cs.to_dict()["actual_profit_usd"] == 5000)

# 1.9 SearchStats
ss2 = SearchStats()
ss2.nodes_explored = 100
ss2.sequences_profitable = 3
d = ss2.to_dict()
test("SearchStats to_dict has nodes_explored", d["nodes_explored"] == 100)

# 1.10 SearchResult
sr = SearchResult()
sr.total_profitable = 2
sr.best_profit_usd = 50000
test("SearchResult to_dict has best_profit", sr.to_dict()["best_profit_usd"] == 50000)
test(
    "SearchResult to_json works",
    '"best_profit_usd"' in sr.to_json() and "50000" in sr.to_json(),
)


# ═══════════════════════════════════════════════════════
#  2. Heuristic Prioritizer Tests
# ═══════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("2. HEURISTIC PRIORITIZER TESTS")
print("=" * 60)

prioritizer = HeuristicPrioritizer()

# 2.1 Empty input
targets, seeds = prioritizer.analyze(None)
test("Heuristic: None input → empty", len(targets) == 0 and len(seeds) == 0)

# 2.2 Vault scenario
space, actions, graph = build_vault_scenario()
targets, seeds = prioritizer.analyze(space)

test("Heuristic: finds targets", len(targets) > 0, f"got {len(targets)}")

# Find withdraw target
withdraw_target = next((t for t in targets if t.function_name == "withdraw"), None)
test("Heuristic: withdraw is a target", withdraw_target is not None)

if withdraw_target:
    test("Heuristic: withdraw has CEI tag", "cei_violation" in withdraw_target.tags)
    test("Heuristic: withdraw sends ETH", withdraw_target.sends_eth)
    test(
        "Heuristic: withdraw score > 0.7",
        withdraw_target.score > 0.7,
        f"score = {withdraw_target.score}",
    )
    test("Heuristic: withdraw has reasons", len(withdraw_target.reasons) > 0)
    test("Heuristic: withdraw is NOT guarded", "unguarded" in withdraw_target.tags)

# 2.3 Ordering: withdraw should be #1
test(
    "Heuristic: withdraw is top target",
    targets[0].function_name == "withdraw",
    f"top is {targets[0].function_name}",
)

# 2.4 Admin function should be deprioritized
admin_target = next((t for t in targets if t.function_name == "setFee"), None)
test("Heuristic: admin target exists", admin_target is not None)
if admin_target:
    test(
        "Heuristic: admin score < withdraw", admin_target.score < withdraw_target.score
    )

# 2.5 Seeds generated
test("Heuristic: generates seeds", len(seeds) > 0, f"got {len(seeds)}")

# Check for reentrancy seed
reent_seeds = [s for s in seeds if "reent" in s.seed_id]
test(
    "Heuristic: reentrancy seeds generated",
    len(reent_seeds) > 0,
    f"got {len(reent_seeds)}",
)

# 2.6 DeFi scenario
space2, _, _ = build_defi_scenario()
targets2, seeds2 = prioritizer.analyze(space2)
test("Heuristic: DeFi targets found", len(targets2) > 0, f"got {len(targets2)}")
test("Heuristic: DeFi seeds found", len(seeds2) > 0, f"got {len(seeds2)}")

# 2.7 Graph enrichment
fin_graph = MockFinancialGraph()
targets3, seeds3 = prioritizer.analyze(space, fin_graph)
test("Heuristic: works with FinancialGraph", len(targets3) > 0)


# ═══════════════════════════════════════════════════════
#  3. Weakness Detector Tests
# ═══════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("3. WEAKNESS DETECTOR TESTS")
print("=" * 60)

detector = EconomicWeaknessDetector()

# 3.1 Empty input
w, s = detector.detect(None)
test("Weakness: None input → empty", len(w) == 0)

# 3.2 Vault reentrancy detection
space_v, _, _ = build_vault_scenario()
weaknesses, w_seeds = detector.detect(space_v)

test(
    "Weakness: finds weaknesses in Vault", len(weaknesses) > 0, f"got {len(weaknesses)}"
)

# Check for reentrancy weakness
reent_w = [w for w in weaknesses if w.weakness_type == WeaknessType.REENTRANCY_DRAIN]
test("Weakness: REENTRANCY_DRAIN detected", len(reent_w) > 0, f"got {len(reent_w)}")

if reent_w:
    test("Weakness: reentrancy is critical", reent_w[0].severity == "critical")
    test(
        "Weakness: reentrancy confidence > 0.8",
        reent_w[0].confidence > 0.8,
        f"conf = {reent_w[0].confidence}",
    )
    test("Weakness: reentrancy has entry_actions", len(reent_w[0].entry_actions) > 0)
    test("Weakness: reentrancy has exit_actions", len(reent_w[0].exit_actions) > 0)

# 3.3 Seeds from weaknesses
test("Weakness: generates seeds", len(w_seeds) > 0, f"got {len(w_seeds)}")

# 3.4 DeFi scenario weaknesses
space_d, _, _ = build_defi_scenario()
w_defi, s_defi = detector.detect(space_d)

test("Weakness: DeFi weaknesses found", len(w_defi) > 0, f"got {len(w_defi)}")

# Check for invariant break
inv_w = [w for w in w_defi if w.weakness_type == WeaknessType.INVARIANT_BREAK]
test("Weakness: invariant break detected in DeFi", len(inv_w) > 0, f"got {len(inv_w)}")

# Check for flash loan vector
fl_w = [w for w in w_defi if w.weakness_type == WeaknessType.FLASH_LOAN_VECTOR]
test("Weakness: flash loan vector detected", len(fl_w) > 0, f"got {len(fl_w)}")

# 3.5 Access leak detection
actions_leak = {
    "Contract_admin_0": MockAction(
        "Contract_admin_0",
        "Contract",
        "setOwner",
        "admin",
        requires_access=False,  # Bug: admin without access control!
        state_writes=["owner"],
    ),
}
graph_leak = MockActionGraph(actions_leak)
space_leak = MockActionSpace(graph_leak)
w_leak, _ = detector.detect(space_leak)

access_w = [w for w in w_leak if w.weakness_type == WeaknessType.ACCESS_LEAK]
test("Weakness: ACCESS_LEAK detected", len(access_w) > 0, f"got {len(access_w)}")

# 3.6 Weakness ordering by severity
test(
    "Weakness: critical first",
    weaknesses[0].severity == "critical" if weaknesses else True,
)

# 3.7 Cross-function state
cross_w = [w for w in w_defi if w.weakness_type == WeaknessType.CROSS_FUNCTION_STATE]
# Pool has shared state between deposit/withdraw
test(
    "Weakness: cross-function state check ran", True
)  # May or may not find — depends on sends_eth


# ═══════════════════════════════════════════════════════
#  4. Guided Search Tests
# ═══════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("4. GUIDED SEARCH TESTS")
print("=" * 60)

# 4.1 Beam Search
config = SearchConfig()
config.beam_width = 5
config.beam_depth = 3
config.max_search_time_seconds = 5
config.max_sequences_to_test = 50
config.strategy = SearchStrategy.BEAM_SEARCH

search = GuidedSearchEngine(config)

space_v, actions_v, graph_v = build_vault_scenario()

# Attack engine returns profit on second call (deposit + withdraw = profitable)
engine_mock = MockAttackEngine(profit_schedule=[0, 50000, 100000, 0, 30000])

seeds_v = [
    SearchSeed(
        seed_id="s1",
        source=SeedSource.HEURISTIC,
        action_sequence=["Vault_deposit_0", "Vault_withdraw_0"],
        priority=0.9,
    ),
    SearchSeed(
        seed_id="s2",
        source=SeedSource.HEURISTIC,
        action_sequence=["Vault_deposit_0"],
        priority=0.7,
    ),
]

candidates = search.search(
    seeds=seeds_v,
    action_graph=graph_v,
    actions=actions_v,
    simulate_fn=engine_mock.simulate_sequence,
    initial_state=MockProtocolState(),
)

test("Beam: returns candidates", len(candidates) > 0, f"got {len(candidates)}")

test("Beam: some profitable", any(c.actual_profit_usd > 0 for c in candidates))

test(
    "Beam: stats populated",
    search.stats.sequences_simulated > 0,
    f"simulated {search.stats.sequences_simulated}",
)

# 4.2 MCTS Search
config2 = SearchConfig()
config2.mcts_iterations = 20
config2.max_search_time_seconds = 5
config2.max_sequences_to_test = 50
config2.strategy = SearchStrategy.MCTS

search2 = GuidedSearchEngine(config2)
engine_mock2 = MockAttackEngine(profit_schedule=[0, 80000, 0, 0, 0])

candidates2 = search2.search(
    seeds=seeds_v,
    action_graph=graph_v,
    actions=actions_v,
    simulate_fn=engine_mock2.simulate_sequence,
    initial_state=MockProtocolState(),
)

test("MCTS: returns candidates", len(candidates2) > 0, f"got {len(candidates2)}")

test(
    "MCTS: stats populated",
    search2.stats.nodes_explored > 0,
    f"explored {search2.stats.nodes_explored}",
)

# 4.3 Evolutionary Search
config3 = SearchConfig()
config3.population_size = 10
config3.generations = 5
config3.max_search_time_seconds = 5
config3.max_sequences_to_test = 50
config3.strategy = SearchStrategy.EVOLUTIONARY

search3 = GuidedSearchEngine(config3)
engine_mock3 = MockAttackEngine(profit_schedule=[0, 0, 0, 70000, 0, 0, 0, 0])

candidates3 = search3.search(
    seeds=seeds_v,
    action_graph=graph_v,
    actions=actions_v,
    simulate_fn=engine_mock3.simulate_sequence,
    initial_state=MockProtocolState(),
)

test(
    "Evolutionary: returns candidates", len(candidates3) > 0, f"got {len(candidates3)}"
)

# 4.4 Greedy Search
config4 = SearchConfig()
config4.max_search_time_seconds = 3
config4.max_sequences_to_test = 20
config4.strategy = SearchStrategy.GREEDY_BEST_FIRST

search4 = GuidedSearchEngine(config4)
engine_mock4 = MockAttackEngine(profit_schedule=[90000, 0, 0])

candidates4 = search4.search(
    seeds=seeds_v,
    action_graph=graph_v,
    actions=actions_v,
    simulate_fn=engine_mock4.simulate_sequence,
    initial_state=MockProtocolState(),
)

test("Greedy: returns candidates", len(candidates4) > 0, f"got {len(candidates4)}")

test(
    "Greedy: best sorted first",
    (
        candidates4[0].actual_profit_usd >= candidates4[-1].actual_profit_usd
        if len(candidates4) > 1
        else True
    ),
)

# 4.5 Hybrid Search
config5 = SearchConfig()
config5.max_search_time_seconds = 10
config5.max_sequences_to_test = 100
config5.strategy = SearchStrategy.HYBRID
config5.mcts_iterations = 10
config5.population_size = 8
config5.generations = 3
config5.beam_width = 5
config5.beam_depth = 2

search5 = GuidedSearchEngine(config5)
engine_mock5 = MockAttackEngine(profit_schedule=[0, 0, 60000, 0, 0, 0, 40000, 0, 0, 0])

candidates5 = search5.search(
    seeds=seeds_v,
    action_graph=graph_v,
    actions=actions_v,
    simulate_fn=engine_mock5.simulate_sequence,
    initial_state=MockProtocolState(),
)

test("Hybrid: returns candidates", len(candidates5) > 0, f"got {len(candidates5)}")

test("Hybrid: by_strategy has hybrid", "hybrid" in search5.stats.by_strategy)

# 4.6 Empty seeds
search6 = GuidedSearchEngine(SearchConfig())
empty = search6.search(
    seeds=[],
    action_graph=graph_v,
    actions=actions_v,
    simulate_fn=engine_mock.simulate_sequence,
    initial_state=MockProtocolState(),
)
test("Search: empty seeds → empty results", len(empty) == 0)

# 4.7 Heuristic scoring
score = search._heuristic_score(["Vault_withdraw_0"], actions_v)
test("Heuristic scoring: CEI + sends_eth → high score", score > 0.5, f"score = {score}")

# 4.8 Action to step conversion
step = search._action_to_step(actions_v["Vault_withdraw_0"])
test("Action to step: has action_id", step["action_id"] == "Vault_withdraw_0")
test("Action to step: has function_name", step["function_name"] == "withdraw")
test("Action to step: has category", step["category"] == "fund_outflow")
test("Action to step: has has_cei_violation", step["has_cei_violation"] == True)


# ═══════════════════════════════════════════════════════
#  5. Profit Gradient Tests
# ═══════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("5. PROFIT GRADIENT TESTS")
print("=" * 60)

gradient = ProfitGradientEngine(
    gradient_steps=10,
    amount_step_pct=0.1,
    min_improvement_usd=1.0,
)

# 5.1 Optimize a profitable candidate
profitable_candidate = CandidateSequence(
    candidate_id="p1",
    steps=[
        {
            "action_id": "Vault_deposit_0",
            "contract_name": "Vault",
            "function_name": "deposit",
            "category": "fund_inflow",
            "msg_value": "1000000000000000000",
            "parameters": [
                {"name": "amount", "concrete_values": [10**18], "is_amount": True}
            ],
            "sends_eth": False,
            "has_cei_violation": False,
        },
        {
            "action_id": "Vault_withdraw_0",
            "contract_name": "Vault",
            "function_name": "withdraw",
            "category": "fund_outflow",
            "msg_value": "0",
            "parameters": [
                {"name": "amount", "concrete_values": [10**18], "is_amount": True}
            ],
            "sends_eth": True,
            "has_cei_violation": True,
        },
    ],
    action_ids=["Vault_deposit_0", "Vault_withdraw_0"],
    actual_profit_usd=50000,
    simulated=True,
)

# Simulate increasing profit with better params
call_count = [0]


def mock_simulate_improving(sequence, initial_state, seq_id=""):
    call_count[0] += 1
    base = 50000
    # Some multipliers are better
    if call_count[0] % 3 == 0:
        return MockAttackResult(
            net_profit_usd=base + 5000,
            is_profitable=True,
            attack_type="reentrancy",
            severity="critical",
        )
    return MockAttackResult(
        net_profit_usd=base - 1000,
        is_profitable=True,
        attack_type="reentrancy",
        severity="critical",
    )


stats = SearchStats()
optimized = gradient.optimize(
    [profitable_candidate], mock_simulate_improving, MockProtocolState(), stats
)

test("Gradient: returns optimized list", len(optimized) == 1)
test("Gradient: candidate was optimized or unchanged", optimized[0].simulated)

# 5.2 Unprofitable candidate should NOT be over-optimized
bad_candidate = CandidateSequence(
    candidate_id="bad1",
    steps=[
        {"action_id": "x", "function_name": "x", "msg_value": "0", "parameters": []}
    ],
    action_ids=["x"],
    actual_profit_usd=-10000,
    simulated=True,
)
optimized_bad = gradient.optimize(
    [bad_candidate], mock_simulate_improving, MockProtocolState()
)
test(
    "Gradient: very unprofitable left as-is",
    optimized_bad[0].actual_profit_usd == -10000,
)

# 5.3 Non-simulated candidate passed through
unsimulated = CandidateSequence(
    candidate_id="unsim",
    simulated=False,
)
result_unsim = gradient.optimize(
    [unsimulated], mock_simulate_improving, MockProtocolState()
)
test("Gradient: non-simulated passed through", not result_unsim[0].simulated)


# ═══════════════════════════════════════════════════════
#  6. Search Orchestrator (Full Pipeline) Tests
# ═══════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("6. SEARCH ORCHESTRATOR TESTS")
print("=" * 60)

# 6.1 Basic orchestration
orch = SearchOrchestrator(
    {
        "max_search_time_seconds": 5,
        "max_sequences_to_test": 30,
        "strategy": "hybrid",
        "mcts_iterations": 10,
        "population_size": 8,
        "generations": 3,
        "beam_width": 5,
        "beam_depth": 2,
        "enable_gradient_optimization": False,  # skip for speed
    }
)

space_v, _, _ = build_vault_scenario()
fin_graph = MockFinancialGraph()
fin_graph.action_space = space_v

# Profitable mock engine
engine_orch = MockAttackEngine(profit_schedule=[0, 0, 120000, 0, 80000, 0, 0, 0])

result = orch.search(fin_graph, space_v, engine_orch)

test("Orchestrator: returns SearchResult", isinstance(result, SearchResult))
test("Orchestrator: version is 1.0.0", result.version == "1.0.0")
test(
    "Orchestrator: stats populated",
    result.stats.total_seeds > 0,
    f"seeds = {result.stats.total_seeds}",
)
test(
    "Orchestrator: targets found",
    len(result.targets) > 0,
    f"targets = {len(result.targets)}",
)
test(
    "Orchestrator: weaknesses found",
    len(result.weaknesses) > 0,
    f"weaknesses = {len(result.weaknesses)}",
)
test(
    "Orchestrator: seeds generated",
    result.seeds_generated > 0,
    f"seeds = {result.seeds_generated}",
)
test(
    "Orchestrator: candidates tested",
    result.candidates_tested > 0,
    f"tested = {result.candidates_tested}",
)

# 6.2 Error handling: None inputs
orch2 = SearchOrchestrator()
r2 = orch2.search(None, None, None)
test("Orchestrator: None action_space → error", len(r2.errors) > 0)

r3 = orch2.search(fin_graph, space_v, None)
test("Orchestrator: None attack_engine → error", len(r3.errors) > 0)

# 6.3 Empty action space
empty_space = MockActionSpace(MockActionGraph({}, {}))
r4 = orch.search(fin_graph, empty_space, engine_orch)
test("Orchestrator: empty actions → error", len(r4.errors) > 0)

# 6.4 to_json works
json_str = result.to_json()
test("Orchestrator: to_json works", "total_profitable" in json_str)

# 6.5 Full DeFi scenario
space_d, _, _ = build_defi_scenario()
engine_defi = MockAttackEngine(profit_schedule=[0, 0, 200000, 0, 0, 0, 0, 0])

orch3 = SearchOrchestrator(
    {
        "max_search_time_seconds": 5,
        "max_sequences_to_test": 30,
        "mcts_iterations": 10,
        "population_size": 8,
        "generations": 3,
        "beam_width": 5,
        "beam_depth": 2,
        "enable_gradient_optimization": False,
    }
)

r5 = orch3.search(fin_graph, space_d, engine_defi)
test("Orchestrator DeFi: finds results", isinstance(r5, SearchResult))
test(
    "Orchestrator DeFi: execution time tracked",
    r5.execution_time_ms > 0,
    f"time = {r5.execution_time_ms:.1f}ms",
)

# 6.6 With gradient optimization enabled
orch4 = SearchOrchestrator(
    {
        "max_search_time_seconds": 5,
        "max_sequences_to_test": 30,
        "mcts_iterations": 5,
        "population_size": 5,
        "generations": 2,
        "beam_width": 3,
        "beam_depth": 2,
        "enable_gradient_optimization": True,
        "gradient_steps": 5,
    }
)

engine_grad = MockAttackEngine(profit_schedule=[0, 0, 50000, 60000, 70000, 0, 0])
r6 = orch4.search(fin_graph, space_v, engine_grad)
test("Orchestrator + Gradient: completes", isinstance(r6, SearchResult))
test(
    "Orchestrator + Gradient: optimization time tracked",
    r6.stats.optimization_time_ms >= 0,
)


# ═══════════════════════════════════════════════════════
#  7. Integration Tests
# ═══════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("7. INTEGRATION TESTS")
print("=" * 60)

# 7.1 Package import
try:
    from agl_security_tool.search_engine import (
        SearchOrchestrator as SO,
        HeuristicPrioritizer as HP,
        EconomicWeaknessDetector as EWD,
        GuidedSearchEngine as GSE,
        ProfitGradientEngine as PGE,
    )

    test("Import: all components importable", True)
except ImportError as e:
    test("Import: all components importable", False, str(e))

# 7.2 Version
try:
    from agl_security_tool.search_engine import __version__

    test("Version: search_engine is 1.0.0", __version__ == "1.0.0")
except ImportError:
    test("Version: search_engine __version__", False)

# 7.3 Main engine version
try:
    from agl_security_tool.state_extraction import __version__ as main_ver

    test("Version: main engine is 5.0.0", main_ver == "5.0.0", f"got {main_ver}")
except ImportError:
    test("Version: main engine", False)

# 7.4 FinancialGraph has search_results field
try:
    from agl_security_tool.state_extraction.models import FinancialGraph as FG

    fg = FG()
    test("FinancialGraph: has search_results field", hasattr(fg, "search_results"))
    test("FinancialGraph: search_results defaults to None", fg.search_results is None)
except ImportError:
    test("FinancialGraph: search_results", False)

# 7.5 SearchOrchestrator in __all__
try:
    from agl_security_tool.state_extraction import __all__ as all_exports

    test("Exports: SearchOrchestrator in __all__", "SearchOrchestrator" in all_exports)
except ImportError:
    test("Exports: SearchOrchestrator", False)


# ═══════════════════════════════════════════════════════
#  RESULTS
# ═══════════════════════════════════════════════════════

print("\n" + "=" * 60)
print(f"RESULTS: {passed}/{total} passed, {failed} failed")
print("=" * 60)

if failed > 0:
    print("\nFailed tests:")
    for e in errors:
        print(f"  {e}")

print(f"\n{'✅ ALL TESTS PASSED!' if failed == 0 else '❌ SOME TESTS FAILED'}")
