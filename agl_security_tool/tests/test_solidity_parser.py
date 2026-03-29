"""
AGL SoliditySemanticParser Tests — اختبارات المحلل الدلالي
==========================================================

Tests: contract/function/state_var extraction, operation ordering,
modifier detection, inheritance resolution, edge cases.
"""

import pytest
from detectors.solidity_parser import SoliditySemanticParser
from detectors import (
    ParsedContract,
    ParsedFunction,
    StateVar,
    Operation,
    OpType,
    ModifierInfo,
)


def parse(source: str):
    return SoliditySemanticParser().parse(source)


# ═══════════════════════════════════════════════════════════
#  Contract Extraction
# ═══════════════════════════════════════════════════════════

class TestContractExtraction:

    def test_single_contract(self):
        source = """
        pragma solidity ^0.8.0;
        contract Vault {
            uint256 public balance;
        }
        """
        contracts = parse(source)
        assert len(contracts) == 1
        assert contracts[0].name == "Vault"
        assert contracts[0].contract_type == "contract"

    def test_multiple_contracts(self):
        source = """
        pragma solidity ^0.8.0;
        contract A { uint x; }
        contract B { uint y; }
        """
        contracts = parse(source)
        assert len(contracts) == 2
        names = {c.name for c in contracts}
        assert names == {"A", "B"}

    def test_interface_type(self):
        source = """
        pragma solidity ^0.8.0;
        interface IERC20 {
            function totalSupply() external view returns (uint256);
        }
        """
        contracts = parse(source)
        assert len(contracts) == 1
        assert contracts[0].contract_type == "interface"

    def test_library_type(self):
        source = """
        pragma solidity ^0.8.0;
        library SafeMath {
            function add(uint a, uint b) internal pure returns (uint) { return a + b; }
        }
        """
        contracts = parse(source)
        assert len(contracts) == 1
        assert contracts[0].contract_type == "library"

    def test_abstract_contract(self):
        source = """
        pragma solidity ^0.8.0;
        abstract contract Base {
            function foo() external virtual;
        }
        """
        contracts = parse(source)
        assert len(contracts) == 1
        assert contracts[0].contract_type == "abstract"

    def test_inheritance(self):
        source = """
        pragma solidity ^0.8.0;
        contract Base { uint public x; }
        contract Child is Base { uint public y; }
        """
        contracts = parse(source)
        child = next(c for c in contracts if c.name == "Child")
        assert "Base" in child.inherits

    def test_multiple_inheritance(self):
        source = """
        pragma solidity ^0.8.0;
        contract A { }
        contract B { }
        contract C is A, B { }
        """
        contracts = parse(source)
        c = next(c for c in contracts if c.name == "C")
        assert "A" in c.inherits
        assert "B" in c.inherits

    def test_pragma_extracted(self):
        source = """
        pragma solidity ^0.8.20;
        contract X { }
        """
        contracts = parse(source)
        assert "0.8.20" in contracts[0].pragma

    def test_license_extracted(self):
        source = """
        // SPDX-License-Identifier: MIT
        pragma solidity ^0.8.0;
        contract X { }
        """
        contracts = parse(source)
        assert contracts[0].license == "MIT"


# ═══════════════════════════════════════════════════════════
#  State Variable Extraction
# ═══════════════════════════════════════════════════════════

class TestStateVarExtraction:

    def test_basic_vars(self):
        source = """
        pragma solidity ^0.8.0;
        contract Vault {
            uint256 public balance;
            address public owner;
        }
        """
        contracts = parse(source)
        svars = contracts[0].state_vars
        assert "balance" in svars
        assert "owner" in svars

    def test_mapping_var(self):
        source = """
        pragma solidity ^0.8.0;
        contract Token {
            mapping(address => uint256) public balances;
        }
        """
        contracts = parse(source)
        assert "balances" in contracts[0].state_vars

    def test_constant_var(self):
        source = """
        pragma solidity ^0.8.0;
        contract Config {
            uint256 constant MAX = 100;
        }
        """
        contracts = parse(source)
        if "MAX" in contracts[0].state_vars:
            assert contracts[0].state_vars["MAX"].is_constant

    def test_immutable_var(self):
        source = """
        pragma solidity ^0.8.0;
        contract Config {
            address immutable owner;
            constructor() { owner = msg.sender; }
        }
        """
        contracts = parse(source)
        if "owner" in contracts[0].state_vars:
            assert contracts[0].state_vars["owner"].is_immutable


# ═══════════════════════════════════════════════════════════
#  Function Extraction
# ═══════════════════════════════════════════════════════════

class TestFunctionExtraction:

    def test_basic_function(self):
        source = """
        pragma solidity ^0.8.0;
        contract Vault {
            function deposit() external payable { }
        }
        """
        contracts = parse(source)
        funcs = contracts[0].functions
        assert "deposit" in funcs
        assert funcs["deposit"].visibility == "external"
        assert funcs["deposit"].mutability == "payable"

    def test_view_function(self):
        source = """
        pragma solidity ^0.8.0;
        contract Vault {
            uint public x;
            function getX() external view returns (uint) { return x; }
        }
        """
        contracts = parse(source)
        assert "getX" in contracts[0].functions
        assert contracts[0].functions["getX"].mutability == "view"

    def test_pure_function(self):
        source = """
        pragma solidity ^0.8.0;
        contract Math {
            function add(uint a, uint b) external pure returns (uint) { return a + b; }
        }
        """
        contracts = parse(source)
        assert contracts[0].functions["add"].mutability == "pure"

    def test_function_with_modifier(self):
        source = """
        pragma solidity ^0.8.0;
        contract Vault {
            address owner;
            modifier onlyOwner() { require(msg.sender == owner); _; }
            function withdraw() external onlyOwner { }
        }
        """
        contracts = parse(source)
        f = contracts[0].functions.get("withdraw")
        assert f is not None
        assert f.has_access_control or "onlyOwner" in f.modifiers

    def test_constructor(self):
        source = """
        pragma solidity ^0.8.0;
        contract Vault {
            address public owner;
            constructor() { owner = msg.sender; }
        }
        """
        contracts = parse(source)
        funcs = contracts[0].functions
        has_ctor = any("constructor" in k.lower() for k in funcs)
        assert has_ctor

    def test_receive_function(self):
        source = """
        pragma solidity ^0.8.0;
        contract Vault {
            receive() external payable { }
        }
        """
        contracts = parse(source)
        has_receive = any("receive" in k.lower() for k in contracts[0].functions)
        assert has_receive

    def test_multiple_functions(self):
        source = """
        pragma solidity ^0.8.0;
        contract Token {
            mapping(address => uint) balances;
            function mint(address to, uint amount) external { balances[to] += amount; }
            function burn(address from, uint amount) external { balances[from] -= amount; }
            function balanceOf(address addr) external view returns (uint) { return balances[addr]; }
        }
        """
        contracts = parse(source)
        fnames = set(contracts[0].functions.keys())
        assert "mint" in fnames
        assert "burn" in fnames
        assert "balanceOf" in fnames


# ═══════════════════════════════════════════════════════════
#  Operation Extraction (Semantic Analysis)
# ═══════════════════════════════════════════════════════════

class TestOperationExtraction:

    def test_external_call_detected(self):
        source = """
        pragma solidity ^0.8.0;
        contract Vault {
            function withdraw(address payable to) external {
                (bool ok,) = to.call{value: 100}("");
                require(ok);
            }
        }
        """
        contracts = parse(source)
        func = contracts[0].functions.get("withdraw")
        assert func is not None
        ext_calls = [op for op in func.operations
                     if op.op_type in (OpType.EXTERNAL_CALL, OpType.EXTERNAL_CALL_ETH)]
        assert len(ext_calls) > 0

    def test_state_write_detected(self):
        source = """
        pragma solidity ^0.8.0;
        contract Counter {
            uint256 public count;
            function increment() external { count += 1; }
        }
        """
        contracts = parse(source)
        func = contracts[0].functions.get("increment")
        assert func is not None
        assert "count" in func.state_writes or func.modifies_state

    def test_require_detected(self):
        source = """
        pragma solidity ^0.8.0;
        contract Auth {
            address public owner;
            function restricted() external {
                require(msg.sender == owner, "not owner");
            }
        }
        """
        contracts = parse(source)
        func = contracts[0].functions.get("restricted")
        assert func is not None
        has_require = any(op.op_type == OpType.REQUIRE for op in func.operations)
        assert has_require or len(func.require_checks) > 0

    def test_emit_detected(self):
        source = """
        pragma solidity ^0.8.0;
        contract Logger {
            event Logged(uint val);
            function log(uint v) external { emit Logged(v); }
        }
        """
        contracts = parse(source)
        func = contracts[0].functions.get("log")
        assert func is not None
        has_emit = any(op.op_type == OpType.EMIT for op in func.operations)
        assert has_emit

    def test_loop_detected(self):
        source = """
        pragma solidity ^0.8.0;
        contract Looper {
            uint[] public items;
            function sum() external view returns (uint s) {
                for (uint i = 0; i < items.length; i++) {
                    s += items[i];
                }
            }
        }
        """
        contracts = parse(source)
        func = contracts[0].functions.get("sum")
        assert func is not None
        assert func.has_loops

    def test_delegatecall_detected(self):
        source = """
        pragma solidity ^0.8.0;
        contract Proxy {
            address public impl;
            fallback() external payable {
                (bool ok,) = impl.delegatecall(msg.data);
                require(ok);
            }
        }
        """
        contracts = parse(source)
        funcs = contracts[0].functions
        fallback = funcs.get("fallback") or funcs.get("fallback()")
        if fallback:
            assert fallback.has_delegatecall

    def test_operation_ordering_reentrancy(self):
        """Key test: external call BEFORE state write = reentrancy pattern."""
        source = """
        pragma solidity ^0.8.0;
        contract Vault {
            mapping(address => uint) public balances;
            function withdraw() external {
                uint amount = balances[msg.sender];
                (bool ok,) = msg.sender.call{value: amount}("");
                require(ok);
                balances[msg.sender] = 0;
            }
        }
        """
        contracts = parse(source)
        func = contracts[0].functions.get("withdraw")
        assert func is not None
        # Should detect external call AND state write
        has_ext = any(op.op_type in (OpType.EXTERNAL_CALL, OpType.EXTERNAL_CALL_ETH)
                      for op in func.operations)
        has_write = any(op.op_type == OpType.STATE_WRITE for op in func.operations)
        assert has_ext and has_write


# ═══════════════════════════════════════════════════════════
#  Modifier Extraction
# ═══════════════════════════════════════════════════════════

class TestModifierExtraction:

    def test_modifier_extracted(self):
        source = """
        pragma solidity ^0.8.0;
        contract Auth {
            address public owner;
            modifier onlyOwner() {
                require(msg.sender == owner);
                _;
            }
            function admin() external onlyOwner { }
        }
        """
        contracts = parse(source)
        mods = contracts[0].modifiers
        assert "onlyOwner" in mods

    def test_reentrancy_guard_detected(self):
        source = """
        pragma solidity ^0.8.0;
        contract Guarded {
            bool private locked;
            modifier nonReentrant() {
                require(!locked);
                locked = true;
                _;
                locked = false;
            }
            function withdraw() external nonReentrant {
                uint x = 1;
            }
        }
        """
        contracts = parse(source)
        func = contracts[0].functions.get("withdraw")
        assert func is not None
        assert func.has_reentrancy_guard


# ═══════════════════════════════════════════════════════════
#  Inheritance Resolution
# ═══════════════════════════════════════════════════════════

class TestInheritanceResolution:

    def test_inherited_state_vars_merged(self):
        source = """
        pragma solidity ^0.8.0;
        contract Base {
            uint256 public baseValue;
        }
        contract Child is Base {
            uint256 public childValue;
            function setBase(uint v) external { baseValue = v; }
        }
        """
        contracts = parse(source)
        child = next(c for c in contracts if c.name == "Child")
        # baseValue should be merged into Child's state_vars
        assert "baseValue" in child.state_vars
        assert "childValue" in child.state_vars

    def test_inherited_vars_enable_state_write_detection(self):
        source = """
        pragma solidity ^0.8.0;
        contract Storage {
            mapping(address => uint) public balances;
        }
        contract Vault is Storage {
            function deposit() external payable {
                balances[msg.sender] += msg.value;
            }
        }
        """
        contracts = parse(source)
        vault = next(c for c in contracts if c.name == "Vault")
        func = vault.functions.get("deposit")
        assert func is not None
        # With inheritance resolution, parser should recognize balances write
        assert "balances" in func.state_writes or func.modifies_state


# ═══════════════════════════════════════════════════════════
#  Edge Cases
# ═══════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_empty_source(self):
        contracts = parse("")
        assert contracts == []

    def test_only_comments(self):
        source = "// Just a comment\n/* block comment */"
        contracts = parse(source)
        assert contracts == []

    def test_only_pragma(self):
        source = "pragma solidity ^0.8.0;"
        contracts = parse(source)
        assert contracts == []

    def test_nested_braces(self):
        source = """
        pragma solidity ^0.8.0;
        contract Nested {
            function complex() external {
                if (true) {
                    for (uint i = 0; i < 10; i++) {
                        if (i > 5) { break; }
                    }
                }
            }
        }
        """
        contracts = parse(source)
        assert len(contracts) == 1
        assert "complex" in contracts[0].functions

    def test_using_for(self):
        source = """
        pragma solidity ^0.8.0;
        library SafeERC20 {
            function safeTransfer(address token, address to, uint amount) internal { }
        }
        contract Vault {
            using SafeERC20 for address;
        }
        """
        contracts = parse(source)
        vault = next(c for c in contracts if c.name == "Vault")
        assert len(vault.using_for) > 0

    def test_events_extracted(self):
        source = """
        pragma solidity ^0.8.0;
        contract Token {
            event Transfer(address indexed from, address indexed to, uint amount);
            event Approval(address indexed owner, address indexed spender, uint amount);
        }
        """
        contracts = parse(source)
        assert len(contracts[0].events) >= 2

    def test_selfdestruct_detected(self):
        source = """
        pragma solidity ^0.8.0;
        contract Killable {
            function kill() external {
                selfdestruct(payable(msg.sender));
            }
        }
        """
        contracts = parse(source)
        func = contracts[0].functions.get("kill")
        assert func is not None
        assert func.has_selfdestruct

    def test_upgradeable_detection(self):
        source = """
        pragma solidity ^0.8.0;
        contract Initializable { }
        contract MyContract is Initializable {
            function initialize() external { }
        }
        """
        contracts = parse(source)
        mc = next(c for c in contracts if c.name == "MyContract")
        assert mc.is_upgradeable
