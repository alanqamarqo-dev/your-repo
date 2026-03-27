"""
Comprehensive unit tests for all 22 AGL security detectors.

Tests cover every detector class with purpose-built ParsedContract fixtures:
  - Reentrancy: ETH, NoETH, ReadOnly, CrossFunction
  - Access Control: UnprotectedWithdraw, UnprotectedSelfDestruct, TxOriginAuth,
                    DangerousDelegatecall
  - DeFi: FirstDepositorAttack, OracleManipulation, PriceStaleCheck,
          DivideBeforeMultiply, FlashLoanCallbackValidation
  - Common: UncheckedLowLevelCall, UnboundedLoop, DuplicateCondition,
            ShadowedStateVariable, EncodePacked, MissingEventEmission
  - Token: UncheckedERC20Transfer, ArbitrarySendERC20, FeeOnTransferToken
  - DetectorRunner orchestration
"""

import os
import sys

import pytest

_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, _PROJECT_ROOT)

from agl_security_tool.detectors import (
    ParsedContract,
    ParsedFunction,
    Operation,
    OpType,
    StateVar,
    ModifierInfo,
    Finding,
    Severity,
    Confidence,
    DetectorRunner,
)
from agl_security_tool.detectors.reentrancy import (
    ReentrancyETH,
    ReentrancyNoETH,
    ReentrancyReadOnly,
    ReentrancyCrossFunction,
)
from agl_security_tool.detectors.access_control import (
    UnprotectedWithdraw,
    UnprotectedSelfDestruct,
    TxOriginAuth,
    DangerousDelegatecall,
)
from agl_security_tool.detectors.defi import (
    FirstDepositorAttack,
    OracleManipulation,
    PriceStaleCheck,
    DivideBeforeMultiply,
    FlashLoanCallbackValidation,
)
from agl_security_tool.detectors.common import (
    UncheckedLowLevelCall,
    UnboundedLoop,
    DuplicateCondition,
    ShadowedStateVariable,
    EncodePacked,
    MissingEventEmission,
)
from agl_security_tool.detectors.token import (
    UncheckedERC20Transfer,
    ArbitrarySendERC20,
    FeeOnTransferToken,
)


# ═══════════════════════════════════════════════════════════
#  Fixture Helpers
# ═══════════════════════════════════════════════════════════


def _make_contract(name="TestContract", functions=None, state_vars=None,
                   modifiers=None, contract_type="contract", using_for=None,
                   inherits=None, events=None):
    """Build a minimal ParsedContract for testing."""
    c = ParsedContract(name=name)
    c.contract_type = contract_type
    c.functions = functions or {}
    c.state_vars = state_vars or {}
    c.modifiers = modifiers or {}
    c.using_for = using_for or []
    c.inherits = inherits or []
    c.events = events or []
    return c


def _make_function(name="testFunc", visibility="public", mutability="",
                   operations=None, state_reads=None, state_writes=None,
                   external_calls=None, has_reentrancy_guard=False,
                   has_access_control=False, sends_eth=False,
                   modifies_state=False, has_selfdestruct=False,
                   has_delegatecall=False, raw_body="",
                   parameters=None, modifiers=None,
                   require_checks=None, has_loops=False,
                   is_constructor=False, line_start=10, line_end=50):
    """Build a minimal ParsedFunction for testing."""
    f = ParsedFunction(name=name)
    f.visibility = visibility
    f.mutability = mutability
    f.operations = operations or []
    f.state_reads = state_reads or []
    f.state_writes = state_writes or []
    f.external_calls = external_calls or []
    f.has_reentrancy_guard = has_reentrancy_guard
    f.has_access_control = has_access_control
    f.sends_eth = sends_eth
    f.modifies_state = modifies_state
    f.has_selfdestruct = has_selfdestruct
    f.has_delegatecall = has_delegatecall
    f.raw_body = raw_body
    f.parameters = parameters or []
    f.modifiers = modifiers or []
    f.require_checks = require_checks or []
    f.has_loops = has_loops
    f.is_constructor = is_constructor
    f.line_start = line_start
    f.line_end = line_end
    return f


def _make_op(op_type, line=10, target="", details="", sends_eth=False,
             in_loop=False, raw_text=""):
    return Operation(
        op_type=op_type, line=line, target=target, details=details,
        sends_eth=sends_eth, in_loop=in_loop, raw_text=raw_text,
    )


# ═══════════════════════════════════════════════════════════
#  Reentrancy Detectors
# ═══════════════════════════════════════════════════════════


class TestReentrancyETH:
    """Tests for REENTRANCY-ETH detector."""

    def test_detects_eth_call_before_state_write(self):
        """Classic reentrancy: .call{value}() then state write."""
        func = _make_function(
            "withdraw",
            operations=[
                _make_op(OpType.EXTERNAL_CALL_ETH, line=20, target="msg.sender"),
                _make_op(OpType.STATE_WRITE, line=25, target="balances"),
            ],
        )
        contract = _make_contract(functions={"withdraw": func})
        detector = ReentrancyETH()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1
        assert findings[0].severity == Severity.CRITICAL

    def test_safe_with_reentrancy_guard(self):
        """No detection when nonReentrant modifier is present."""
        func = _make_function(
            "withdraw",
            has_reentrancy_guard=True,
            operations=[
                _make_op(OpType.EXTERNAL_CALL_ETH, line=20, target="msg.sender"),
                _make_op(OpType.STATE_WRITE, line=25, target="balances"),
            ],
        )
        contract = _make_contract(functions={"withdraw": func})
        detector = ReentrancyETH()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_safe_state_write_before_call(self):
        """No detection when state is written before the call (CEI pattern)."""
        func = _make_function(
            "withdraw",
            operations=[
                _make_op(OpType.STATE_WRITE, line=20, target="balances"),
                _make_op(OpType.EXTERNAL_CALL_ETH, line=25, target="msg.sender"),
            ],
        )
        contract = _make_contract(functions={"withdraw": func})
        detector = ReentrancyETH()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_view_functions_ignored(self):
        func = _make_function(
            "getBalance", mutability="view",
            operations=[
                _make_op(OpType.EXTERNAL_CALL_ETH, line=20, target="msg.sender"),
                _make_op(OpType.STATE_WRITE, line=25, target="balances"),
            ],
        )
        contract = _make_contract(functions={"getBalance": func})
        detector = ReentrancyETH()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_no_external_call_no_finding(self):
        func = _make_function(
            "withdraw",
            operations=[
                _make_op(OpType.STATE_WRITE, line=20, target="balances"),
            ],
        )
        contract = _make_contract(functions={"withdraw": func})
        detector = ReentrancyETH()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestReentrancyNoETH:
    """Tests for REENTRANCY-NO-ETH detector."""

    def test_detects_external_call_before_state_write(self):
        func = _make_function(
            "transfer",
            operations=[
                _make_op(OpType.EXTERNAL_CALL, line=20, target="token", details="transfer"),
                _make_op(OpType.STATE_WRITE, line=25, target="balances"),
            ],
        )
        contract = _make_contract(functions={"transfer": func})
        detector = ReentrancyNoETH()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1
        assert findings[0].severity == Severity.HIGH

    def test_safe_with_guard(self):
        func = _make_function(
            "transfer",
            has_reentrancy_guard=True,
            operations=[
                _make_op(OpType.EXTERNAL_CALL, line=20, target="token"),
                _make_op(OpType.STATE_WRITE, line=25, target="balances"),
            ],
        )
        contract = _make_contract(functions={"transfer": func})
        detector = ReentrancyNoETH()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestReentrancyReadOnly:
    """Tests for REENTRANCY-READ-ONLY detector."""

    def test_detects_view_reading_shared_state(self):
        """View function reads state modified by caller with external call."""
        withdraw = _make_function(
            "withdraw", visibility="public",
            external_calls=[_make_op(OpType.EXTERNAL_CALL_ETH, line=20, target="msg.sender")],
            state_writes=["totalAssets"],
            operations=[
                _make_op(OpType.EXTERNAL_CALL_ETH, line=20, target="msg.sender"),
                _make_op(OpType.STATE_WRITE, line=25, target="totalAssets"),
            ],
        )
        get_price = _make_function(
            "getPrice", visibility="public", mutability="view",
            state_reads=["totalAssets"],
        )
        contract = _make_contract(functions={
            "withdraw": withdraw,
            "getPrice": get_price,
        })
        detector = ReentrancyReadOnly()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_no_finding_when_view_has_guard(self):
        withdraw = _make_function(
            "withdraw", visibility="public",
            external_calls=[_make_op(OpType.EXTERNAL_CALL_ETH, line=20)],
            state_writes=["totalAssets"],
            operations=[
                _make_op(OpType.EXTERNAL_CALL_ETH, line=20),
                _make_op(OpType.STATE_WRITE, line=25, target="totalAssets"),
            ],
        )
        get_price = _make_function(
            "getPrice", mutability="view", has_reentrancy_guard=True,
            state_reads=["totalAssets"],
        )
        contract = _make_contract(functions={"withdraw": withdraw, "getPrice": get_price})
        detector = ReentrancyReadOnly()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestReentrancyCrossFunction:
    """Tests for REENTRANCY-CROSS-FUNCTION detector."""

    def test_detects_cross_function_reentrancy(self):
        withdraw = _make_function(
            "withdraw", visibility="public",
            external_calls=[_make_op(OpType.EXTERNAL_CALL_ETH, line=20)],
            state_reads=["balances"], state_writes=["balances"],
            operations=[
                _make_op(OpType.EXTERNAL_CALL_ETH, line=20, target="msg.sender"),
                _make_op(OpType.STATE_WRITE, line=25, target="balances"),
            ],
        )
        deposit = _make_function(
            "deposit", visibility="public",
            state_reads=["balances"], state_writes=["balances"],
            modifies_state=True,
        )
        contract = _make_contract(functions={"withdraw": withdraw, "deposit": deposit})
        detector = ReentrancyCrossFunction()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_when_both_have_guards(self):
        withdraw = _make_function(
            "withdraw", visibility="public", has_reentrancy_guard=True,
            external_calls=[_make_op(OpType.EXTERNAL_CALL_ETH, line=20)],
            state_reads=["balances"], state_writes=["balances"],
            operations=[
                _make_op(OpType.EXTERNAL_CALL_ETH, line=20),
                _make_op(OpType.STATE_WRITE, line=25, target="balances"),
            ],
        )
        deposit = _make_function(
            "deposit", visibility="public", has_reentrancy_guard=True,
            state_reads=["balances"], state_writes=["balances"],
            modifies_state=True,
        )
        contract = _make_contract(functions={"withdraw": withdraw, "deposit": deposit})
        detector = ReentrancyCrossFunction()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


# ═══════════════════════════════════════════════════════════
#  Access Control Detectors
# ═══════════════════════════════════════════════════════════


class TestUnprotectedWithdraw:
    def test_detects_unprotected_withdraw(self):
        func = _make_function(
            "withdraw", visibility="public",
            sends_eth=True,
        )
        contract = _make_contract(functions={"withdraw": func})
        detector = UnprotectedWithdraw()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1
        assert findings[0].severity == Severity.CRITICAL

    def test_safe_with_access_control(self):
        func = _make_function(
            "withdraw", visibility="public",
            sends_eth=True, has_access_control=True,
        )
        contract = _make_contract(functions={"withdraw": func})
        detector = UnprotectedWithdraw()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_internal_functions_ignored(self):
        func = _make_function(
            "withdraw", visibility="internal",
            sends_eth=True,
        )
        contract = _make_contract(functions={"withdraw": func})
        detector = UnprotectedWithdraw()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_constructor_ignored(self):
        func = _make_function(
            "withdraw", visibility="public",
            sends_eth=True, is_constructor=True,
        )
        contract = _make_contract(functions={"withdraw": func})
        detector = UnprotectedWithdraw()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestUnprotectedSelfDestruct:
    def test_detects_unprotected_selfdestruct(self):
        func = _make_function(
            "kill", visibility="public",
            has_selfdestruct=True,
        )
        contract = _make_contract(functions={"kill": func})
        detector = UnprotectedSelfDestruct()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1
        assert findings[0].severity == Severity.CRITICAL

    def test_safe_with_access_control(self):
        func = _make_function(
            "kill", visibility="public",
            has_selfdestruct=True, has_access_control=True,
        )
        contract = _make_contract(functions={"kill": func})
        detector = UnprotectedSelfDestruct()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_private_function_safe(self):
        func = _make_function(
            "kill", visibility="private",
            has_selfdestruct=True,
        )
        contract = _make_contract(functions={"kill": func})
        detector = UnprotectedSelfDestruct()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestTxOriginAuth:
    def test_detects_tx_origin_in_require(self):
        func = _make_function(
            "admin", visibility="public",
            operations=[
                _make_op(OpType.REQUIRE, line=15,
                         target="require(tx.origin == owner)"),
            ],
        )
        contract = _make_contract(functions={"admin": func})
        detector = TxOriginAuth()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1
        assert findings[0].severity == Severity.HIGH

    def test_safe_msg_sender(self):
        func = _make_function(
            "admin", visibility="public",
            operations=[
                _make_op(OpType.REQUIRE, line=15,
                         target="require(msg.sender == owner)"),
            ],
        )
        contract = _make_contract(functions={"admin": func})
        detector = TxOriginAuth()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_detects_tx_origin_outside_require(self):
        func = _make_function(
            "admin", visibility="public",
            operations=[
                _make_op(OpType.STATE_WRITE, line=15,
                         raw_text="if (tx.origin == owner) { ... }"),
            ],
        )
        contract = _make_contract(functions={"admin": func})
        detector = TxOriginAuth()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1


class TestDangerousDelegatecall:
    def test_detects_user_controlled_delegatecall(self):
        func = _make_function(
            "execute", visibility="public",
            has_delegatecall=True,
            parameters=[{"name": "target", "type": "address"}],
            operations=[
                _make_op(OpType.DELEGATECALL, line=20, target="target"),
            ],
        )
        contract = _make_contract(functions={"execute": func})
        detector = DangerousDelegatecall()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1
        assert findings[0].severity == Severity.CRITICAL

    def test_detects_mutable_state_delegatecall(self):
        func = _make_function(
            "execute", visibility="public",
            has_delegatecall=True,
            operations=[
                _make_op(OpType.DELEGATECALL, line=20, target="implementation"),
            ],
        )
        state_vars = {
            "implementation": StateVar(
                name="implementation", var_type="address",
                is_constant=False, is_immutable=False,
            ),
        }
        contract = _make_contract(functions={"execute": func}, state_vars=state_vars)
        detector = DangerousDelegatecall()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_constant_address(self):
        func = _make_function(
            "execute", visibility="public",
            has_delegatecall=True,
            operations=[
                _make_op(OpType.DELEGATECALL, line=20, target="implementation"),
            ],
        )
        state_vars = {
            "implementation": StateVar(
                name="implementation", var_type="address",
                is_constant=True, is_immutable=False,
            ),
        }
        contract = _make_contract(functions={"execute": func}, state_vars=state_vars)
        detector = DangerousDelegatecall()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_no_delegatecall_no_finding(self):
        func = _make_function("execute", visibility="public", has_delegatecall=False)
        contract = _make_contract(functions={"execute": func})
        detector = DangerousDelegatecall()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


# ═══════════════════════════════════════════════════════════
#  DeFi Detectors
# ═══════════════════════════════════════════════════════════


class TestFirstDepositorAttack:
    def test_detects_vulnerable_deposit(self):
        func = _make_function(
            "deposit", visibility="public",
            raw_body="shares = amount * totalSupply / totalAssets;\n",
        )
        contract = _make_contract(functions={"deposit": func})
        detector = FirstDepositorAttack()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_with_virtual_offset(self):
        func = _make_function(
            "deposit", visibility="public",
            raw_body="shares = amount * totalSupply / totalAssets;\n"
                     "_decimalsOffset = 6;\n",
        )
        contract = _make_contract(functions={"deposit": func})
        detector = FirstDepositorAttack()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_non_deposit_function_ignored(self):
        func = _make_function(
            "swap", visibility="public",
            raw_body="shares = amount * totalSupply / totalAssets;\n",
        )
        contract = _make_contract(functions={"swap": func})
        detector = FirstDepositorAttack()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestOracleManipulation:
    def test_detects_spot_price_usage(self):
        func = _make_function(
            "getPrice", visibility="public",
            raw_body="(,,,,) = pool.slot0();\n",
        )
        contract = _make_contract(functions={"getPrice": func})
        detector = OracleManipulation()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_with_twap(self):
        func = _make_function(
            "getPrice", visibility="public",
            raw_body="price = pool.observe(3600);\nresult = pool.slot0();\n",
        )
        contract = _make_contract(functions={"getPrice": func})
        detector = OracleManipulation()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_detects_getReserves(self):
        func = _make_function(
            "swap", visibility="public",
            raw_body="(r0, r1,) = pair.getReserves();\n",
        )
        contract = _make_contract(functions={"swap": func})
        detector = OracleManipulation()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1


class TestPriceStaleCheck:
    def test_detects_missing_staleness_check(self):
        func = _make_function(
            "getPrice", visibility="public",
            raw_body="(, int256 price, , , ) = feed.latestRoundData();\nreturn price;\n",
        )
        contract = _make_contract(functions={"getPrice": func})
        detector = PriceStaleCheck()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_with_staleness_check(self):
        func = _make_function(
            "getPrice", visibility="public",
            raw_body=(
                "(, int256 price, , uint256 updatedAt, ) = feed.latestRoundData();\n"
                "require(updatedAt > block.timestamp - 3600);\n"
                "require(price > 0);\n"
            ),
        )
        contract = _make_contract(functions={"getPrice": func})
        detector = PriceStaleCheck()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_no_latestRoundData_no_finding(self):
        func = _make_function(
            "getPrice", visibility="public",
            raw_body="return oracle.getPrice();\n",
        )
        contract = _make_contract(functions={"getPrice": func})
        detector = PriceStaleCheck()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestDivideBeforeMultiply:
    def test_detects_divide_before_multiply(self):
        func = _make_function(
            "calc", visibility="public",
            raw_body="result = a / b * c;\n",
        )
        contract = _make_contract(functions={"calc": func})
        detector = DivideBeforeMultiply()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_multiply_first(self):
        func = _make_function(
            "calc", visibility="public",
            raw_body="result = a * c / b;\n",
        )
        contract = _make_contract(functions={"calc": func})
        detector = DivideBeforeMultiply()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_safe_mulDiv(self):
        func = _make_function(
            "calc", visibility="public",
            raw_body="result = FullMath.mulDiv(a / b * c, d, e);\n",
        )
        contract = _make_contract(functions={"calc": func})
        detector = DivideBeforeMultiply()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestFlashLoanCallbackValidation:
    def test_detects_unvalidated_callback(self):
        func = _make_function(
            "executeOperation", visibility="external",
            raw_body="// do stuff\n",
            require_checks=[],
        )
        contract = _make_contract(functions={"executeOperation": func})
        detector = FlashLoanCallbackValidation()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_with_sender_check(self):
        func = _make_function(
            "executeOperation", visibility="external",
            raw_body="require(msg.sender == address(POOL));\n",
            require_checks=["msg.sender == address(POOL)"],
        )
        contract = _make_contract(functions={"executeOperation": func})
        detector = FlashLoanCallbackValidation()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_non_callback_function_ignored(self):
        func = _make_function(
            "deposit", visibility="external",
            raw_body="// do stuff\n",
        )
        contract = _make_contract(functions={"deposit": func})
        detector = FlashLoanCallbackValidation()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_detects_multiple_callback_patterns(self):
        """Test all callback names are recognized."""
        callbacks = ["onFlashLoan", "uniswapV2Call", "receiveFlashLoan"]
        detector = FlashLoanCallbackValidation()

        for cb_name in callbacks:
            func = _make_function(cb_name, visibility="external", raw_body="// no check\n")
            contract = _make_contract(functions={cb_name: func})
            findings = detector.detect(contract, [contract])
            assert len(findings) >= 1, f"Expected finding for callback {cb_name}"


# ═══════════════════════════════════════════════════════════
#  Common Detectors
# ═══════════════════════════════════════════════════════════


class TestUncheckedLowLevelCall:
    def test_detects_unchecked_call(self):
        func = _make_function(
            "send", visibility="public",
            operations=[
                _make_op(OpType.EXTERNAL_CALL_ETH, line=20, target="addr",
                         raw_text='addr.call{value: amount}("")'),
            ],
        )
        contract = _make_contract(functions={"send": func})
        detector = UncheckedLowLevelCall()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_with_bool_check(self):
        func = _make_function(
            "send", visibility="public",
            operations=[
                _make_op(OpType.EXTERNAL_CALL_ETH, line=20, target="addr",
                         raw_text='(bool success,) = addr.call{value: amount}("")'),
                _make_op(OpType.REQUIRE, line=21, target="success"),
            ],
        )
        contract = _make_contract(functions={"send": func})
        detector = UncheckedLowLevelCall()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_non_call_operations_ignored(self):
        func = _make_function(
            "update", visibility="public",
            operations=[
                _make_op(OpType.STATE_WRITE, line=20, target="x"),
            ],
        )
        contract = _make_contract(functions={"update": func})
        detector = UncheckedLowLevelCall()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestUnboundedLoop:
    def test_detects_unbounded_loop(self):
        func = _make_function(
            "distribute", visibility="public",
            raw_body="for (uint i = 0; i < users.length; i++) {\n  users[i].transfer(1);\n}\n",
        )
        state_vars = {
            "users": StateVar(name="users", var_type="address[]", is_array=True),
        }
        contract = _make_contract(functions={"distribute": func}, state_vars=state_vars)
        detector = UnboundedLoop()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_with_max_limit(self):
        func = _make_function(
            "distribute", visibility="public",
            raw_body=(
                "require(users.length < MAX_LENGTH);\n"
                "for (uint i = 0; i < users.length; i++) {\n}\n"
            ),
        )
        state_vars = {
            "users": StateVar(name="users", var_type="address[]", is_array=True),
        }
        contract = _make_contract(functions={"distribute": func}, state_vars=state_vars)
        detector = UnboundedLoop()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_constant_bound_safe(self):
        func = _make_function(
            "process", visibility="public",
            raw_body="for (uint i = 0; i < 10; i++) {\n}\n",
        )
        contract = _make_contract(functions={"process": func})
        detector = UnboundedLoop()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestDuplicateCondition:
    def test_detects_duplicate_in_and(self):
        func = _make_function(
            "check", visibility="public",
            raw_body="require(x > 0 && x > 0);\n",
        )
        contract = _make_contract(functions={"check": func})
        detector = DuplicateCondition()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_detects_duplicate_in_or(self):
        func = _make_function(
            "check", visibility="public",
            raw_body="if (a == b || a == b) { revert(); }\n",
        )
        contract = _make_contract(functions={"check": func})
        detector = DuplicateCondition()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_no_duplicate(self):
        func = _make_function(
            "check", visibility="public",
            raw_body="require(x > 0 && y > 0);\n",
        )
        contract = _make_contract(functions={"check": func})
        detector = DuplicateCondition()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_detects_repeated_require(self):
        func = _make_function(
            "check", visibility="public",
            operations=[
                _make_op(OpType.REQUIRE, line=10, target="x > 0"),
                _make_op(OpType.REQUIRE, line=15, target="x > 0"),
            ],
        )
        contract = _make_contract(functions={"check": func})
        detector = DuplicateCondition()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1


class TestShadowedStateVariable:
    def test_detects_local_shadowing(self):
        func = _make_function(
            "update", visibility="public",
            raw_body="uint256 balance = 0;\n",
        )
        state_vars = {
            "balance": StateVar(name="balance", var_type="uint256", line=5),
        }
        contract = _make_contract(functions={"update": func}, state_vars=state_vars)
        detector = ShadowedStateVariable()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_detects_parameter_shadowing(self):
        func = _make_function(
            "setBalance", visibility="public",
            parameters=[{"name": "balance", "type": "uint256"}],
        )
        state_vars = {
            "balance": StateVar(name="balance", var_type="uint256", line=5),
        }
        contract = _make_contract(functions={"setBalance": func}, state_vars=state_vars)
        detector = ShadowedStateVariable()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_constructor_shadowing_ignored(self):
        func = _make_function(
            "constructor", visibility="public", is_constructor=True,
            raw_body="uint256 balance = 0;\n",
        )
        state_vars = {
            "balance": StateVar(name="balance", var_type="uint256", line=5),
        }
        contract = _make_contract(functions={"constructor": func}, state_vars=state_vars)
        detector = ShadowedStateVariable()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestEncodePacked:
    def test_detects_encode_packed_with_multiple_args(self):
        func = _make_function(
            "hash", visibility="public",
            raw_body='keccak256(abi.encodePacked(name, data));\n',
            parameters=[
                {"name": "name", "type": "string"},
                {"name": "data", "type": "bytes"},
            ],
        )
        contract = _make_contract(functions={"hash": func})
        detector = EncodePacked()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_single_arg(self):
        func = _make_function(
            "hash", visibility="public",
            raw_body='keccak256(abi.encodePacked(value));\n',
        )
        contract = _make_contract(functions={"hash": func})
        detector = EncodePacked()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestMissingEventEmission:
    def test_detects_setter_without_event(self):
        func = _make_function(
            "setOwner", visibility="public",
            modifies_state=True,
            state_writes=["owner"],
            operations=[
                _make_op(OpType.STATE_WRITE, line=15, target="owner"),
            ],
        )
        contract = _make_contract(functions={"setOwner": func})
        detector = MissingEventEmission()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_with_emit(self):
        func = _make_function(
            "setOwner", visibility="public",
            modifies_state=True,
            state_writes=["owner"],
            operations=[
                _make_op(OpType.STATE_WRITE, line=15, target="owner"),
                _make_op(OpType.EMIT, line=16),
            ],
        )
        contract = _make_contract(functions={"setOwner": func})
        detector = MissingEventEmission()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_view_function_ignored(self):
        func = _make_function(
            "setOwner", visibility="public", mutability="view",
            modifies_state=False,
        )
        contract = _make_contract(functions={"setOwner": func})
        detector = MissingEventEmission()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_private_function_ignored(self):
        func = _make_function(
            "setOwner", visibility="private",
            modifies_state=True, state_writes=["owner"],
        )
        contract = _make_contract(functions={"setOwner": func})
        detector = MissingEventEmission()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


# ═══════════════════════════════════════════════════════════
#  Token Detectors
# ═══════════════════════════════════════════════════════════


class TestUncheckedERC20Transfer:
    def test_detects_unchecked_transfer(self):
        func = _make_function(
            "pay", visibility="public",
            operations=[
                _make_op(OpType.EXTERNAL_CALL, line=20, target="token",
                         details="transfer", raw_text="token.transfer(to, amount)"),
            ],
        )
        contract = _make_contract(functions={"pay": func})
        detector = UncheckedERC20Transfer()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_with_safe_erc20(self):
        func = _make_function(
            "pay", visibility="public",
            operations=[
                _make_op(OpType.EXTERNAL_CALL, line=20, target="token",
                         details="transfer", raw_text="token.transfer(to, amount)"),
            ],
        )
        contract = _make_contract(
            functions={"pay": func},
            using_for=[{"library": "SafeERC20", "type": "IERC20"}],
        )
        detector = UncheckedERC20Transfer()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_safe_with_require_wrapper(self):
        func = _make_function(
            "pay", visibility="public",
            operations=[
                _make_op(OpType.EXTERNAL_CALL, line=20, target="token",
                         details="transfer",
                         raw_text="require(token.transfer(to, amount))"),
            ],
        )
        contract = _make_contract(functions={"pay": func})
        detector = UncheckedERC20Transfer()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestArbitrarySendERC20:
    def test_detects_user_controlled_from(self):
        func = _make_function(
            "move", visibility="public",
            parameters=[{"name": "from", "type": "address"}],
            raw_body="token.transferFrom(from, address(this), amount);\n",
        )
        contract = _make_contract(functions={"move": func})
        detector = ArbitrarySendERC20()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_with_msg_sender(self):
        func = _make_function(
            "deposit", visibility="public",
            raw_body="token.transferFrom(msg.sender, address(this), amount);\n",
        )
        contract = _make_contract(functions={"deposit": func})
        detector = ArbitrarySendERC20()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0

    def test_internal_function_ignored(self):
        func = _make_function(
            "move", visibility="internal",
            parameters=[{"name": "from", "type": "address"}],
            raw_body="token.transferFrom(from, address(this), amount);\n",
        )
        contract = _make_contract(functions={"move": func})
        detector = ArbitrarySendERC20()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


class TestFeeOnTransferToken:
    def test_detects_fee_on_transfer_issue(self):
        func = _make_function(
            "deposit", visibility="public",
            raw_body=(
                "token.transferFrom(sender, address(this), amount);\n"
                "balances[sender] += amount;\n"
            ),
        )
        contract = _make_contract(functions={"deposit": func})
        detector = FeeOnTransferToken()
        findings = detector.detect(contract, [contract])
        assert len(findings) >= 1

    def test_safe_with_balance_check(self):
        func = _make_function(
            "deposit", visibility="public",
            raw_body=(
                "uint256 before = token.balanceOf( address( this ) );\n"
                "token.transferFrom(sender, address(this), amount);\n"
                "uint256 received = token.balanceOf( address( this ) ) - before;\n"
            ),
        )
        contract = _make_contract(functions={"deposit": func})
        detector = FeeOnTransferToken()
        findings = detector.detect(contract, [contract])
        assert len(findings) == 0


# ═══════════════════════════════════════════════════════════
#  DetectorRunner
# ═══════════════════════════════════════════════════════════


class TestDetectorRunner:
    def test_all_detectors_registered(self):
        runner = DetectorRunner()
        assert len(runner.detectors) == 22

    def test_list_detectors(self):
        runner = DetectorRunner()
        detectors_list = runner.list_detectors()
        assert len(detectors_list) == 22
        for d in detectors_list:
            assert "id" in d
            assert "title" in d
            assert "severity" in d

    def test_run_on_empty_contracts(self):
        runner = DetectorRunner()
        findings = runner.run([])
        assert findings == []

    def test_run_skips_interfaces(self):
        contract = _make_contract(name="IVault", contract_type="interface")
        runner = DetectorRunner()
        findings = runner.run([contract])
        assert len(findings) == 0

    def test_run_single_detector(self):
        func = _make_function(
            "withdraw", visibility="public", sends_eth=True,
        )
        contract = _make_contract(functions={"withdraw": func})
        runner = DetectorRunner()
        findings = runner.run_single("UNPROTECTED-WITHDRAW", [contract])
        assert len(findings) >= 1

    def test_run_single_unknown_detector(self):
        contract = _make_contract()
        runner = DetectorRunner()
        findings = runner.run_single("NONEXISTENT-DETECTOR", [contract])
        assert findings == []

    def test_findings_sorted_by_severity(self):
        """Findings should be sorted: critical first, then high, etc."""
        withdraw = _make_function("withdraw", visibility="public", sends_eth=True)
        admin = _make_function(
            "admin", visibility="public",
            operations=[
                _make_op(OpType.REQUIRE, line=15, target="require(tx.origin == owner)"),
            ],
        )
        contract = _make_contract(functions={"withdraw": withdraw, "admin": admin})
        runner = DetectorRunner()
        findings = runner.run([contract])
        if len(findings) >= 2:
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
            for i in range(len(findings) - 1):
                s1 = severity_order.get(findings[i].severity.value, 5)
                s2 = severity_order.get(findings[i + 1].severity.value, 5)
                assert s1 <= s2

    def test_detector_error_handling(self):
        """If a detector throws an exception, the runner records it."""
        contract = _make_contract(
            functions={"test": _make_function("test")},
        )
        runner = DetectorRunner()
        # Normal run should not crash
        findings = runner.run([contract])
        # Should return without crashing regardless of individual detector errors
        assert isinstance(findings, list)


# ═══════════════════════════════════════════════════════════
#  Finding Data Class
# ═══════════════════════════════════════════════════════════


class TestFinding:
    def test_to_dict(self):
        f = Finding(
            detector_id="TEST-001",
            title="Test finding",
            description="A test",
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            contract="TestContract",
            function="testFunc",
            line=42,
        )
        d = f.to_dict()
        assert d["detector"] == "TEST-001"
        assert d["severity"] == "high"
        assert d["confidence"] == "medium"
        assert d["line"] == 42

    def test_to_dict_with_extra(self):
        f = Finding(
            detector_id="TEST-001",
            title="Test",
            description="Desc",
            severity=Severity.LOW,
            confidence=Confidence.LOW,
            contract="C",
            extra={"key": "value"},
        )
        d = f.to_dict()
        assert d["extra"] == {"key": "value"}

    def test_to_dict_without_extra(self):
        f = Finding(
            detector_id="TEST-001",
            title="Test",
            description="Desc",
            severity=Severity.LOW,
            confidence=Confidence.LOW,
            contract="C",
        )
        d = f.to_dict()
        assert "extra" not in d
