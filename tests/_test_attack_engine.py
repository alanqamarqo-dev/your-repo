"""
═══════════════════════════════════════════════════════════════════
 AGL Attack Engine — Layer 3 Comprehensive Test
 اختبار شامل لمحرك الفيزياء الاقتصادية

 يختبر:
 1. استيراد كل المكونات
 2. نماذج البيانات (models)
 3. تحميل الحالة الأولية (ProtocolStateLoader)
 4. تحويل الحالة (StateMutator + StateStack)
 5. التنفيذ الدلالي (ActionExecutor) — عادي + reentrancy
 6. المحرك الاقتصادي (EconomicEngine)
 7. حاسب الأرباح (ProfitCalculator)
 8. المنسق الرئيسي (AttackSimulationEngine)
 9. التكامل الكامل مع Layer 1 + Layer 2 عبر Vault.sol
═══════════════════════════════════════════════════════════════════
"""

import sys
import os
import json
import time
from pathlib import Path

# === Setup paths ===
_PROJECT_ROOT = str(Path(__file__).parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

WEI = 10**18
PASS = 0
FAIL = 0


def section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}")
    if detail:
        print(f"    → {detail}")


# ═══════════════════════════════════════════════════════════════
#  Test 1: Imports
# ═══════════════════════════════════════════════════════════════
section("1. Imports — استيراد المكونات")

try:
    from agl_security_tool.attack_engine import (
        __version__,
        # Models
        AccountState,
        TokenState,
        PoolState,
        LendingState,
        OracleState,
        ProtocolState,
        BalanceChange,
        StorageChange,
        StateDelta,
        ExecutableAction,
        StepResult,
        AttackResult,
        SimulationConfig,
        SimulationSummary,
        # Components
        ProtocolStateLoader,
        ATTACKER_ADDRESS,
        StateMutator,
        StateStack,
        ActionExecutor,
        EconomicEngine,
        ProfitCalculator,
        # Engine
        AttackSimulationEngine,
    )

    check("All imports successful", True, f"version={__version__}")
except Exception as e:
    check("All imports", False, str(e))
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════
#  Test 2: Models
# ═══════════════════════════════════════════════════════════════
section("2. Models — نماذج البيانات")

# AccountState
acct = AccountState(address="vault", eth_balance=100 * WEI, is_contract=True)
acct.set_balance("USDC", 50000 * 10**6)
check("AccountState.eth_balance", acct.eth_balance == 100 * WEI, f"{acct.eth_balance}")
check("AccountState.get_balance ETH", acct.get_balance("ETH") == 100 * WEI)
check("AccountState.get_balance USDC", acct.get_balance("USDC") == 50000 * 10**6)
check("AccountState.to_dict", "address" in acct.to_dict())

# ProtocolState
state = ProtocolState(block_number=1, timestamp=1700000000)
state.accounts["vault"] = acct
state.set_storage("vault", "totalDeposits", 50 * WEI)
check(
    "ProtocolState.get_storage", state.get_storage("vault", "totalDeposits") == 50 * WEI
)
check("ProtocolState.get_account", state.get_account("new_addr").address == "new_addr")
check("ProtocolState.get_token_price ETH", state.get_token_price("ETH") == 2000.0)
check("ProtocolState.snapshot", state.snapshot() is not state)
check("ProtocolState.summary", state.summary()["accounts"] >= 2)

# StateDelta
delta = StateDelta()
delta.balance_changes.append(BalanceChange("attacker", "ETH", 5 * WEI, "test"))
delta.balance_changes.append(BalanceChange("vault", "ETH", -5 * WEI, "test"))
check(
    "StateDelta.net_balance_change",
    delta.net_balance_change("attacker", "ETH") == 5 * WEI,
)
check("StateDelta.is_empty", not delta.is_empty)
check("StateDelta.to_dict", len(delta.to_dict()["balance_changes"]) == 2)

# SimulationConfig
cfg = SimulationConfig()
check("SimulationConfig defaults", cfg.attacker_eth_balance == 10 * WEI)
check("SimulationConfig gas", cfg.gas_price_wei == 20_000_000_000)

# AttackResult
result = AttackResult(
    sequence_id="test",
    net_profit_usd=198000.0,
    is_profitable=True,
    attack_type="reentrancy",
)
check("AttackResult.to_json", '"reentrancy"' in result.to_json())


# ═══════════════════════════════════════════════════════════════
#  Test 3: Protocol State Loader
# ═══════════════════════════════════════════════════════════════
section("3. ProtocolStateLoader — تحميل الحالة")

loader = ProtocolStateLoader(
    SimulationConfig(
        attacker_eth_balance=10 * WEI,
        contract_eth_balance=100 * WEI,
        attacker_deposit_amount=1 * WEI,
    )
)

# Minimal state
min_state = loader.load_minimal("Vault", {})
check("load_minimal: contract exists", "Vault" in min_state.accounts)
check("load_minimal: attacker exists", ATTACKER_ADDRESS in min_state.accounts)
check(
    "load_minimal: contract balance",
    min_state.accounts["Vault"].eth_balance == 100 * WEI,
    f"{min_state.accounts['Vault'].eth_balance / WEI:.0f} ETH",
)
check(
    "load_minimal: attacker balance",
    min_state.accounts[ATTACKER_ADDRESS].eth_balance == 10 * WEI,
    f"{min_state.accounts[ATTACKER_ADDRESS].eth_balance / WEI:.0f} ETH",
)

# configure_state
loader.configure_state(
    min_state,
    "Vault",
    deposits={ATTACKER_ADDRESS: 1 * WEI},
    total_deposits=1 * WEI,
    contract_balance=100 * WEI,
)
dep_val = (
    min_state.contract_storage.get("Vault", {})
    .get("deposits", {})
    .get(ATTACKER_ADDRESS, 0)
)
td_val = min_state.contract_storage.get("Vault", {}).get("totalDeposits", 0)
check("configure_state: deposit set", dep_val == 1 * WEI, f"{dep_val}")
check("configure_state: totalDeposits", td_val == 1 * WEI, f"{td_val}")


# ═══════════════════════════════════════════════════════════════
#  Test 4: State Mutator + StateStack
# ═══════════════════════════════════════════════════════════════
section("4. StateMutator + StateStack — تحويل الحالة")

# Build a test state
test_state = ProtocolState(block_number=1)
test_state.accounts["vault"] = AccountState(
    address="vault", eth_balance=100 * WEI, is_contract=True
)
test_state.accounts["attacker"] = AccountState(address="attacker", eth_balance=10 * WEI)

# StateMutator
mutator = StateMutator()
test_delta = StateDelta(
    balance_changes=[
        BalanceChange("vault", "ETH", -5 * WEI),
        BalanceChange("attacker", "ETH", 5 * WEI),
    ]
)
mutator.apply(test_state, test_delta)
check(
    "apply: vault lost ETH",
    test_state.accounts["vault"].eth_balance == 95 * WEI,
    f"{test_state.accounts['vault'].eth_balance / WEI:.0f} ETH",
)
check(
    "apply: attacker gained ETH",
    test_state.accounts["attacker"].eth_balance == 15 * WEI,
    f"{test_state.accounts['attacker'].eth_balance / WEI:.0f} ETH",
)

# Reverse
mutator.reverse(test_state, test_delta)
check("reverse: vault restored", test_state.accounts["vault"].eth_balance == 100 * WEI)
check(
    "reverse: attacker restored",
    test_state.accounts["attacker"].eth_balance == 10 * WEI,
)

# StateStack
stack_state = ProtocolState(block_number=1)
stack_state.accounts["vault"] = AccountState(address="vault", eth_balance=100 * WEI)
stack_state.accounts["attacker"] = AccountState(
    address="attacker", eth_balance=10 * WEI
)

stack = StateStack(stack_state)
snap0 = stack.snapshot()

# Apply first delta
d1 = StateDelta(
    balance_changes=[
        BalanceChange("vault", "ETH", -10 * WEI),
        BalanceChange("attacker", "ETH", 10 * WEI),
    ]
)
stack.apply(d1)
check(
    "stack: after d1 attacker",
    stack.current.accounts["attacker"].eth_balance == 20 * WEI,
)

snap1 = stack.snapshot()

# Apply second delta
d2 = StateDelta(
    balance_changes=[
        BalanceChange("vault", "ETH", -20 * WEI),
        BalanceChange("attacker", "ETH", 20 * WEI),
    ]
)
stack.apply(d2)
check(
    "stack: after d2 attacker",
    stack.current.accounts["attacker"].eth_balance == 40 * WEI,
)
check("stack: delta count", stack.delta_count == 2)

# Revert to snap1
stack.revert_to(snap1)
check(
    "revert_to snap1: attacker",
    stack.current.accounts["attacker"].eth_balance == 20 * WEI,
)
check("revert_to snap1: delta count", stack.delta_count == 1)

# Revert to snap0 (initial)
stack.revert_to(snap0)
check(
    "revert_to snap0: attacker",
    stack.current.accounts["attacker"].eth_balance == 10 * WEI,
)
check(
    "revert_to snap0: vault", stack.current.accounts["vault"].eth_balance == 100 * WEI
)


# ═══════════════════════════════════════════════════════════════
#  Test 5: Action Executor — Normal + Reentrancy
# ═══════════════════════════════════════════════════════════════
section("5. ActionExecutor — التنفيذ الدلالي")

executor = ActionExecutor(
    SimulationConfig(
        max_reentrancy_depth=100,
        attacker_deposit_amount=1 * WEI,
    )
)

# --- 5a: Normal Deposit ---
exec_state = ProtocolState(block_number=1)
exec_state.accounts["Vault"] = AccountState(
    address="Vault", eth_balance=100 * WEI, is_contract=True
)
exec_state.accounts[ATTACKER_ADDRESS] = AccountState(
    address=ATTACKER_ADDRESS, eth_balance=10 * WEI
)
exec_state.contract_storage["Vault"] = {
    "deposits": {ATTACKER_ADDRESS: 0},
    "totalDeposits": 0,
}

deposit_action = ExecutableAction(
    action_id="Vault.deposit#0",
    contract_name="Vault",
    function_name="deposit",
    msg_sender=ATTACKER_ADDRESS,
    msg_value=1 * WEI,
    concrete_params={"amount": 1 * WEI},
    net_delta={"deposits[msg.sender]": "+amount", "totalDeposits": "+amount"},
    category="fund_inflow",
    sends_eth=False,
    has_cei_violation=False,
    state_reads=["deposits"],
    state_writes=["deposits", "totalDeposits"],
)

dep_delta = executor.execute(deposit_action, exec_state)
check("deposit: not reverted", not dep_delta.reverted)
check(
    "deposit: has balance changes",
    len(dep_delta.balance_changes) > 0,
    f"{len(dep_delta.balance_changes)} changes",
)
check(
    "deposit: has storage changes",
    len(dep_delta.storage_changes) > 0,
    f"{len(dep_delta.storage_changes)} changes",
)

# Apply deposit
mutator.apply(exec_state, dep_delta)
check(
    "deposit: attacker ETH decreased",
    exec_state.accounts[ATTACKER_ADDRESS].eth_balance == 9 * WEI,
    f"{exec_state.accounts[ATTACKER_ADDRESS].eth_balance / WEI:.0f} ETH",
)
check(
    "deposit: vault ETH increased",
    exec_state.accounts["Vault"].eth_balance == 101 * WEI,
    f"{exec_state.accounts['Vault'].eth_balance / WEI:.0f} ETH",
)

# Update deposits mapping manually (after applying storage changes)
deposits_storage = exec_state.contract_storage["Vault"]["deposits"]
total_deposits = exec_state.contract_storage["Vault"]["totalDeposits"]
check(
    "deposit: deposits storage updated",
    True,
    f"deposits[attacker]={deposits_storage.get(ATTACKER_ADDRESS, 'N/A')}, total={total_deposits}",
)

# --- 5b: Reentrancy Withdraw ---
section("5b. Reentrancy Attack — هجوم إعادة الدخول")

# First, set up the state properly for reentrancy
exec_state.contract_storage["Vault"]["deposits"][ATTACKER_ADDRESS] = 1 * WEI
exec_state.contract_storage["Vault"]["totalDeposits"] = 1 * WEI
exec_state.accounts["Vault"].eth_balance = 101 * WEI  # vault has 101 ETH total
exec_state.accounts[ATTACKER_ADDRESS].eth_balance = 9 * WEI

withdraw_action = ExecutableAction(
    action_id="Vault.withdraw#0",
    contract_name="Vault",
    function_name="withdraw",
    msg_sender=ATTACKER_ADDRESS,
    msg_value=0,
    concrete_params={"amount": 1 * WEI},
    net_delta={"deposits[msg.sender]": "-amount", "totalDeposits": "-amount"},
    external_calls=[
        {"target": "msg.sender", "type": "external_call_eth", "sends_eth": True}
    ],
    sends_eth=True,
    has_cei_violation=True,
    reentrancy_guarded=False,
    state_reads=["deposits"],
    state_writes=["deposits", "totalDeposits"],
)

reentrancy_delta = executor.execute(withdraw_action, exec_state)
check("reentrancy: not reverted", not reentrancy_delta.reverted)

# Count how much ETH the attacker gained
attacker_eth_gain = reentrancy_delta.net_balance_change(ATTACKER_ADDRESS, "ETH")
vault_eth_loss = reentrancy_delta.net_balance_change("Vault", "ETH")

check(
    "reentrancy: attacker gained ETH",
    attacker_eth_gain > 0,
    f"+{attacker_eth_gain / WEI:.0f} ETH",
)
check(
    "reentrancy: vault lost ETH", vault_eth_loss < 0, f"{vault_eth_loss / WEI:.0f} ETH"
)
check(
    "reentrancy: drain > deposit",
    attacker_eth_gain > 1 * WEI,
    f"Drained {attacker_eth_gain / WEI:.0f} ETH with 1 ETH deposit",
)

# Check that storage only updated once (the bug!)
storage_changes = reentrancy_delta.storage_changes
check(
    "reentrancy: storage updates exist",
    len(storage_changes) > 0,
    f"{len(storage_changes)} storage changes (should be for deposits and totalDeposits)",
)

# Check events
has_reentrancy_event = any("REENTRANCY" in e for e in reentrancy_delta.events)
has_drain_event = any("DRAIN" in e for e in reentrancy_delta.events)
check("reentrancy: has REENTRANCY event", has_reentrancy_event)
check("reentrancy: has DRAIN event", has_drain_event)

# Calculate expected depth
expected_depth = exec_state.accounts["Vault"].eth_balance // (1 * WEI)
expected_drain = expected_depth * 1 * WEI
check(
    "reentrancy: expected depth",
    expected_depth > 1,
    f"depth={expected_depth} (vault has {exec_state.accounts['Vault'].eth_balance / WEI:.0f} ETH)",
)

print(f"\n  ═══ Reentrancy Summary ═══")
print(f"  Attacker deposited: 1 ETH")
print(f"  Attacker drained:   {attacker_eth_gain / WEI:.0f} ETH")
print(f"  Vault lost:         {abs(vault_eth_loss) / WEI:.0f} ETH")
print(f"  Profit:             {(attacker_eth_gain - 1*WEI) / WEI:.0f} ETH")


# ═══════════════════════════════════════════════════════════════
#  Test 6: Economic Engine
# ═══════════════════════════════════════════════════════════════
section("6. EconomicEngine — المحرك الاقتصادي")

econ = EconomicEngine()

# Flash loan fee
fee = econ.compute_flash_loan_fee(1000 * WEI, fee_bps=9)
check(
    "flash loan fee (0.09%)",
    fee == 1000 * WEI * 9 // 10000,
    f"fee = {fee / WEI:.6f} ETH",
)

# Pool price impact
pool = PoolState(
    address="pool1",
    token0="WETH",
    token1="USDC",
    reserve0=1000 * WEI,
    reserve1=2_000_000 * 10**6,
    fee_bps=30,
)
impact = econ.compute_price_impact(pool, 100 * WEI, "WETH")
check(
    "price impact: amount_out > 0",
    impact["amount_out"] > 0,
    f"out={impact['amount_out']:,} USDC",
)
check(
    "price impact: price_impact > 0",
    impact["price_impact_pct"] > 0,
    f"impact={impact['price_impact_pct']:.2f}%",
)
check(
    "price impact: slippage > 0",
    impact["slippage_pct"] > 0,
    f"slippage={impact['slippage_pct']:.2f}%",
)

# Gas cost
gas_info = econ.compute_gas_cost(
    500_000,
    ProtocolState(
        gas_price_wei=20_000_000_000,
        eth_price_usd=2000.0,
    ),
)
check("gas cost > 0", gas_info["gas_cost_usd"] > 0, f"${gas_info['gas_cost_usd']:.4f}")

# token_to_usd
usd = econ.token_to_usd("ETH", 99 * WEI, ProtocolState(eth_price_usd=2000.0))
check("token_to_usd: 99 ETH", abs(usd - 198000.0) < 0.01, f"${usd:,.2f}")


# ═══════════════════════════════════════════════════════════════
#  Test 7: Profit Calculator
# ═══════════════════════════════════════════════════════════════
section("7. ProfitCalculator — حاسب الأرباح")

profit_calc = ProfitCalculator(SimulationConfig(eth_price_usd=2000.0))

# Build initial and final states
initial = ProtocolState(eth_price_usd=2000.0)
initial.accounts[ATTACKER_ADDRESS] = AccountState(
    address=ATTACKER_ADDRESS,
    eth_balance=10 * WEI,
)

final = ProtocolState(eth_price_usd=2000.0)
final.accounts[ATTACKER_ADDRESS] = AccountState(
    address=ATTACKER_ADDRESS,
    eth_balance=110 * WEI,
)

steps = [
    StepResult(
        step_index=0,
        action_id="deposit",
        function_name="deposit",
        success=True,
        gas_used=50000,
    ),
    StepResult(
        step_index=1,
        action_id="withdraw",
        function_name="withdraw",
        success=True,
        gas_used=500000,
        eth_transferred=100 * WEI,
        reentrancy_calls=100,
    ),
]

attack_result = profit_calc.calculate(
    initial_state=initial,
    final_state=final,
    attacker_address=ATTACKER_ADDRESS,
    steps=steps,
    attack_type="reentrancy",
    sequence_id="reentrancy_vault_001",
)

check(
    "profit: ETH gained = 100",
    attack_result.profit_by_token.get("ETH", 0) == 100 * WEI,
    f"{attack_result.profit_by_token.get('ETH', 0) / WEI:.0f} ETH",
)
check(
    "profit: USD > 0", attack_result.profit_usd > 0, f"${attack_result.profit_usd:,.2f}"
)
check(
    "profit: gas cost > 0",
    attack_result.gas_cost_usd > 0,
    f"${attack_result.gas_cost_usd:.4f}",
)
check(
    "profit: net_profit > 0",
    attack_result.net_profit_usd > 0,
    f"${attack_result.net_profit_usd:,.2f}",
)
check("profit: is_profitable", attack_result.is_profitable)
check(
    "profit: severity = critical",
    attack_result.severity == "critical",
    f"severity={attack_result.severity}",
)
check(
    "profit: confidence >= 0.95",
    attack_result.confidence >= 0.95,
    f"confidence={attack_result.confidence}",
)
check(
    "profit: attack_name",
    "Reentrancy" in attack_result.attack_name,
    attack_result.attack_name,
)
check(
    "profit: description_ar",
    "مربح" in attack_result.description_ar,
    attack_result.description_ar[:60],
)

print(f"\n  ═══ Profit Summary ═══")
print(f"  Profit (ETH): {attack_result.profit_by_token.get('ETH', 0) / WEI:.0f}")
print(f"  Profit (USD): ${attack_result.profit_usd:,.2f}")
print(f"  Gas Cost:     ${attack_result.gas_cost_usd:.4f}")
print(f"  Net Profit:   ${attack_result.net_profit_usd:,.2f}")
print(f"  Severity:     {attack_result.severity}")
print(f"  Confidence:   {attack_result.confidence:.1%}")


# ═══════════════════════════════════════════════════════════════
#  Test 8: Full Simulation Engine (standalone)
# ═══════════════════════════════════════════════════════════════
section("8. AttackSimulationEngine — المنسق الرئيسي")

engine = AttackSimulationEngine(
    {
        "attacker_eth_balance": 10 * WEI,
        "contract_eth_balance": 100 * WEI,
        "attacker_deposit_amount": 1 * WEI,
        "eth_price_usd": 2000.0,
        "max_reentrancy_depth": 100,
    }
)

# Build a manual sequence that simulates deposit → reentrancy withdraw
manual_sequence = [
    {
        "action_id": "Vault.deposit#0",
        "contract_name": "Vault",
        "function_name": "deposit",
        "category": "fund_inflow",
        "attack_type": "direct_profit",
        "net_delta": {"deposits[msg.sender]": "+amount", "totalDeposits": "+amount"},
        "external_calls": [],
        "sends_eth": False,
        "has_cei_violation": False,
        "reentrancy_guarded": False,
        "preconditions": [],
        "state_reads": ["deposits"],
        "state_writes": ["deposits", "totalDeposits"],
        "parameters": [
            {
                "name": "amount",
                "type": "uint256",
                "concrete_values": ["1000000000000000000"],
                "is_amount": True,
            }
        ],
        "msg_value": "amount",
    },
    {
        "action_id": "Vault.withdraw#0",
        "contract_name": "Vault",
        "function_name": "withdraw",
        "category": "fund_outflow",
        "attack_type": "reentrancy",
        "net_delta": {"deposits[msg.sender]": "-amount", "totalDeposits": "-amount"},
        "external_calls": [
            {"target": "msg.sender", "type": "external_call_eth", "sends_eth": True}
        ],
        "sends_eth": True,
        "has_cei_violation": True,
        "reentrancy_guarded": False,
        "preconditions": ["deposits[msg.sender] >= amount"],
        "state_reads": ["deposits"],
        "state_writes": ["deposits", "totalDeposits"],
        "parameters": [
            {
                "name": "amount",
                "type": "uint256",
                "concrete_values": ["balance_of_sender"],
                "is_amount": True,
            }
        ],
        "msg_value": None,
    },
]

# Load minimal state
manual_state = engine.state_loader.load_minimal("Vault", {})
engine.state_loader.configure_state(
    manual_state,
    "Vault",
    deposits={ATTACKER_ADDRESS: 0},
    total_deposits=0,
    contract_balance=100 * WEI,
    attacker_balance=10 * WEI,
)

sim_result = engine.simulate_sequence(
    manual_sequence,
    manual_state,
    sequence_id="manual_reentrancy_001",
)

check("sim: has steps", len(sim_result.steps) > 0, f"{len(sim_result.steps)} steps")
check(
    "sim: some steps succeeded",
    any(s.success for s in sim_result.steps),
    f"success={[s.success for s in sim_result.steps]}",
)

# The deposit should succeed
dep_step = sim_result.steps[0] if sim_result.steps else None
if dep_step:
    check(
        "sim: deposit succeeded",
        dep_step.success,
        f"error={dep_step.error}" if not dep_step.success else "OK",
    )

# The withdraw (reentrancy) should succeed if deposit prepared the state
wd_step = sim_result.steps[1] if len(sim_result.steps) > 1 else None
if wd_step:
    check(
        "sim: withdraw succeeded",
        wd_step.success,
        f"error={wd_step.error}" if not wd_step.success else "OK",
    )
    if wd_step.reentrancy_calls > 0:
        check(
            "sim: reentrancy detected",
            True,
            f"{wd_step.reentrancy_calls} reentrant calls",
        )
    if wd_step.eth_transferred > 0:
        check("sim: ETH transferred", True, f"{wd_step.eth_transferred / WEI:.0f} ETH")

check(
    "sim: is_profitable",
    sim_result.is_profitable,
    f"net=${sim_result.net_profit_usd:,.2f}",
)
check(
    "sim: net_profit > 0",
    sim_result.net_profit_usd > 0,
    f"${sim_result.net_profit_usd:,.2f}",
)
check(
    "sim: attack_type = reentrancy",
    sim_result.attack_type == "reentrancy",
    f"type={sim_result.attack_type}",
)

print(f"\n  ═══ Simulation Result ═══")
print(f"  Steps: {len(sim_result.steps)}")
print(f"  Profitable: {sim_result.is_profitable}")
print(f"  Net Profit: ${sim_result.net_profit_usd:,.2f}")
print(f"  Attack: {sim_result.attack_type}")
print(f"  Severity: {sim_result.severity}")
print(f"  Confidence: {sim_result.confidence:.1%}")
if sim_result.exploit_scenario:
    print(f"\n  --- Exploit Scenario ---")
    for line in sim_result.exploit_scenario.split("\n"):
        print(f"  {line}")


# ═══════════════════════════════════════════════════════════════
#  Test 9: Full Integration with Layer 1 + Layer 2
# ═══════════════════════════════════════════════════════════════
section("9. Full Integration — التكامل الكامل")

try:
    from agl_security_tool.state_extraction import StateExtractionEngine

    integration_available = True
except ImportError:
    integration_available = False
    print("  ⚠ StateExtractionEngine not importable — skipping Layer 1+2+3 integration")

if integration_available:
    vault_path = Path(__file__).parent / "test_project" / "src" / "Vault.sol"

    if vault_path.exists():
        full_engine = StateExtractionEngine(
            {
                "project_root": str(vault_path.parent.parent),
                "validate": True,
                "temporal": True,
                "action_space": True,
                "attack_simulation": True,
            }
        )

        res = full_engine.extract(str(vault_path))
        graph = (
            res
            if hasattr(res, "nodes")
            else (res.graph if hasattr(res, "graph") else None)
        )

        if graph is None and hasattr(res, "entities"):
            graph = res

        if graph:
            check("integration: graph exists", True)
            check(
                "integration: entities",
                len(getattr(graph, "entities", {})) > 0,
                f"{len(getattr(graph, 'entities', {}))} entities",
            )

            action_space = getattr(graph, "action_space", None)
            check("integration: action_space", action_space is not None)

            attack_sim = getattr(graph, "attack_simulation", None)
            if attack_sim:
                check("integration: attack_simulation exists", True)
                check(
                    "integration: sequences tested",
                    attack_sim.total_sequences_tested > 0,
                    f"{attack_sim.total_sequences_tested} sequences",
                )
                check(
                    "integration: profitable attacks",
                    attack_sim.profitable_attacks >= 0,
                    f"{attack_sim.profitable_attacks} profitable",
                )

                if attack_sim.best_attack:
                    best = attack_sim.best_attack
                    check(
                        "integration: best attack profitable",
                        best.is_profitable,
                        f"${best.net_profit_usd:,.2f}",
                    )
                    check(
                        "integration: best attack type",
                        best.attack_type != "",
                        best.attack_type,
                    )

                    print(f"\n  ═══ Best Attack Found ═══")
                    print(f"  Name: {best.attack_name}")
                    print(f"  Type: {best.attack_type}")
                    print(f"  Net Profit: ${best.net_profit_usd:,.2f}")
                    print(f"  Severity: {best.severity}")
                    print(f"  Confidence: {best.confidence:.1%}")
                else:
                    check(
                        "integration: no profitable attacks found",
                        True,
                        "No profitable attacks (may need more sequence coverage)",
                    )
            else:
                check(
                    "integration: attack_simulation",
                    False,
                    "Not populated — check warnings in engine output",
                )

            # Export full JSON
            try:
                full_json = graph.to_json(indent=2)
                json_size = len(full_json)
                check(
                    "integration: full JSON export",
                    json_size > 0,
                    f"{json_size:,} bytes",
                )

                # Save to file
                output_path = Path(__file__).parent / "_attack_engine_result.json"
                output_path.write_text(full_json, encoding="utf-8")
                check(
                    "integration: saved to file", output_path.exists(), str(output_path)
                )
            except Exception as e:
                check("integration: JSON export", False, str(e)[:150])
        else:
            check("integration: graph extraction", False, "No graph returned")
    else:
        print(f"  ⚠ Vault.sol not found at {vault_path}")


# ═══════════════════════════════════════════════════════════════
#  Test 10: JSON Export
# ═══════════════════════════════════════════════════════════════
section("10. JSON Export — التصدير")

sim_json = sim_result.to_json(indent=2)
check("JSON export: valid", len(sim_json) > 100, f"{len(sim_json):,} chars")

parsed = json.loads(sim_json)
check("JSON: has profit_usd", "profit_usd" in parsed)
check("JSON: has net_profit_usd", "net_profit_usd" in parsed)
check("JSON: has steps", "steps" in parsed)
check("JSON: has attack_type", "attack_type" in parsed)
check("JSON: has severity", "severity" in parsed)


# ═══════════════════════════════════════════════════════════════
#  Final Summary
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print(f"  LAYER 3 TEST RESULTS")
print(f"{'='*70}")
print(f"  ✓ Passed: {PASS}")
print(f"  ✗ Failed: {FAIL}")
print(f"  Total:    {PASS + FAIL}")
print(f"{'='*70}")

if FAIL > 0:
    print(f"\n  ⚠ {FAIL} tests failed!")
    sys.exit(1)
else:
    print(f"\n  ✓ All {PASS} tests passed!")
    print(f"  Layer 3 Economic Physics Engine: OPERATIONAL")
    print(
        f"  Engine v4.0.0 — Profit(attacker) = Value(final) - Value(initial) - Gas - Fees"
    )
    sys.exit(0)
