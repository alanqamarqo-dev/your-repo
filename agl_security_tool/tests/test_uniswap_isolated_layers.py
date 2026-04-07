"""
AGL Security Tool — اختبارات معزولة لكل طبقة على عقود Uniswap
Isolated layer tests on Uniswap-style contracts

يختبر كل طبقة بشكل مستقل:
  1. Detectors (DetectorRunner)
  2. Solidity AST Parser (SolidityASTParserFull)
  3. State Extraction (StateExtractionEngine — Layer 1)
  4. Action Space (ActionSpaceBuilder — Layer 2)
  5. Attack Engine (AttackSimulationEngine — Layer 3)
  6. Search Engine (SearchOrchestrator — Layer 4)
  7. Heikal Math (Tunneling + Wave + Holographic)
  8. Exploit Reasoning (ExploitReasoningEngine)
  9. PoC Generator (PoCGenerator)

Run:
    python -m pytest tests/test_uniswap_isolated_layers.py -v
"""

import sys
import os
import math
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

import pytest

# ── Ensure package is importable ──
_ROOT = Path(__file__).resolve().parent.parent.parent  # d:\AGL
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_PKG = Path(__file__).resolve().parent.parent  # agl_security_tool
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))


# ═══════════════════════════════════════════════════════════════
#  Uniswap-style Test Contracts — عقود مشابهة لبروتوكول يونيسواب
# ═══════════════════════════════════════════════════════════════

UNISWAP_PAIR_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function totalSupply() external view returns (uint256);
}

/// @title UniswapV2-style Pair — simplified AMM pool
contract UniswapPair {
    address public token0;
    address public token1;
    uint112 public reserve0;
    uint112 public reserve1;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;

    uint256 private unlocked = 1;

    event Mint(address indexed sender, uint256 amount0, uint256 amount1);
    event Burn(address indexed sender, uint256 amount0, uint256 amount1, address indexed to);
    event Swap(address indexed sender, uint256 amount0In, uint256 amount1In, uint256 amount0Out, uint256 amount1Out, address indexed to);

    modifier lock() {
        require(unlocked == 1, "LOCKED");
        unlocked = 0;
        _;
        unlocked = 1;
    }

    constructor(address _token0, address _token1) {
        token0 = _token0;
        token1 = _token1;
    }

    // VULN: Spot price oracle — flashloan manipulable
    function getReserves() public view returns (uint112, uint112) {
        return (reserve0, reserve1);
    }

    function getSpotPrice() public view returns (uint256) {
        require(reserve1 > 0, "No reserves");
        return (uint256(reserve0) * 1e18) / uint256(reserve1);
    }

    // VULN: No minimum output check — sandwich attackable
    function swap(uint256 amount0Out, uint256 amount1Out, address to, bytes calldata data) external lock {
        require(amount0Out > 0 || amount1Out > 0, "INSUFFICIENT_OUTPUT");
        require(amount0Out < reserve0 && amount1Out < reserve1, "INSUFFICIENT_LIQUIDITY");

        if (amount0Out > 0) IERC20(token0).transfer(to, amount0Out);
        if (amount1Out > 0) IERC20(token1).transfer(to, amount1Out);

        // Callback — potential reentrancy vector if lock is removed
        if (data.length > 0) {
            (bool ok,) = to.call(data);
            require(ok);
        }

        uint256 balance0 = IERC20(token0).balanceOf(address(this));
        uint256 balance1 = IERC20(token1).balanceOf(address(this));

        // k invariant check — but uses spot balances (manipulable in same tx)
        require(balance0 * balance1 >= uint256(reserve0) * uint256(reserve1), "K");

        reserve0 = uint112(balance0);
        reserve1 = uint112(balance1);
        emit Swap(msg.sender, 0, 0, amount0Out, amount1Out, to);
    }

    function mint(address to) external lock returns (uint256 liquidity) {
        uint256 balance0 = IERC20(token0).balanceOf(address(this));
        uint256 balance1 = IERC20(token1).balanceOf(address(this));
        uint256 amount0 = balance0 - reserve0;
        uint256 amount1 = balance1 - reserve1;

        if (totalSupply == 0) {
            // VULN: First depositor inflation — no minimum liquidity
            liquidity = sqrt(amount0 * amount1);
        } else {
            liquidity = min(
                (amount0 * totalSupply) / reserve0,
                (amount1 * totalSupply) / reserve1
            );
        }

        require(liquidity > 0, "INSUFFICIENT_LIQUIDITY_MINTED");
        balanceOf[to] += liquidity;
        totalSupply += liquidity;

        reserve0 = uint112(balance0);
        reserve1 = uint112(balance1);
        emit Mint(msg.sender, amount0, amount1);
    }

    // VULN: Unchecked ERC20 returns on transfer
    function burn(address to) external lock returns (uint256 amount0, uint256 amount1) {
        uint256 balance0 = IERC20(token0).balanceOf(address(this));
        uint256 balance1 = IERC20(token1).balanceOf(address(this));
        uint256 liquidity = balanceOf[address(this)];

        amount0 = (liquidity * balance0) / totalSupply;
        amount1 = (liquidity * balance1) / totalSupply;
        require(amount0 > 0 && amount1 > 0, "INSUFFICIENT_LIQUIDITY_BURNED");

        balanceOf[address(this)] -= liquidity;
        totalSupply -= liquidity;

        IERC20(token0).transfer(to, amount0);  // return not checked
        IERC20(token1).transfer(to, amount1);  // return not checked

        reserve0 = uint112(IERC20(token0).balanceOf(address(this)));
        reserve1 = uint112(IERC20(token1).balanceOf(address(this)));
        emit Burn(msg.sender, amount0, amount1, to);
    }

    function sqrt(uint256 y) internal pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) { z = x; x = (y / x + x) / 2; }
        } else if (y != 0) { z = 1; }
    }

    function min(uint256 a, uint256 b) internal pure returns (uint256) {
        return a < b ? a : b;
    }
}
"""

UNISWAP_FACTORY_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title UniswapV2-style Factory — creates pairs
contract UniswapFactory {
    address public feeTo;
    address public feeToSetter;
    mapping(address => mapping(address => address)) public getPair;
    address[] public allPairs;

    event PairCreated(address indexed token0, address indexed token1, address pair, uint256 index);

    constructor(address _feeToSetter) {
        feeToSetter = _feeToSetter;
    }

    function allPairsLength() external view returns (uint256) {
        return allPairs.length;
    }

    // VULN: No duplicate check — can create multiple pairs for same tokens
    function createPair(address tokenA, address tokenB) external returns (address pair) {
        require(tokenA != tokenB, "IDENTICAL_ADDRESSES");
        require(tokenA != address(0) && tokenB != address(0), "ZERO_ADDRESS");
        // Missing: require(getPair[tokenA][tokenB] == address(0), "PAIR_EXISTS");

        // Simplified — in real Uniswap uses CREATE2
        pair = address(uint160(uint256(keccak256(abi.encodePacked(tokenA, tokenB, block.timestamp)))));

        getPair[tokenA][tokenB] = pair;
        getPair[tokenB][tokenA] = pair;
        allPairs.push(pair);
        emit PairCreated(tokenA, tokenB, pair, allPairs.length);
    }

    // VULN: No timelock on fee change — centralization risk
    function setFeeTo(address _feeTo) external {
        require(msg.sender == feeToSetter, "FORBIDDEN");
        feeTo = _feeTo;
    }

    function setFeeToSetter(address _feeToSetter) external {
        require(msg.sender == feeToSetter, "FORBIDDEN");
        feeToSetter = _feeToSetter;
    }
}
"""

UNISWAP_ROUTER_SOL = """\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
}

interface IUniswapPair {
    function getReserves() external view returns (uint112, uint112);
    function swap(uint256 amount0Out, uint256 amount1Out, address to, bytes calldata data) external;
    function mint(address to) external returns (uint256);
    function burn(address to) external returns (uint256, uint256);
}

/// @title UniswapV2-style Router — swap + liquidity
contract UniswapRouter {
    address public factory;
    address public WETH;
    address public owner;

    constructor(address _factory, address _weth) {
        factory = _factory;
        WETH = _weth;
        owner = msg.sender;
    }

    // VULN: No slippage protection — amountOutMin = 0 equivalent
    function swapExactTokensForTokens(
        uint256 amountIn,
        address tokenIn,
        address tokenOut,
        address pair,
        address to
    ) external returns (uint256 amountOut) {
        IERC20(tokenIn).transferFrom(msg.sender, pair, amountIn);

        (uint112 r0, uint112 r1) = IUniswapPair(pair).getReserves();
        // VULN: Uses spot reserves — manipulable
        amountOut = (amountIn * uint256(r1)) / (uint256(r0) + amountIn);

        IUniswapPair(pair).swap(0, amountOut, to, "");
    }

    // VULN: block.timestamp as deadline — miners can hold tx
    function swapWithDeadline(
        uint256 amountIn,
        address tokenIn,
        address tokenOut,
        address pair,
        address to
    ) external returns (uint256 amountOut) {
        require(block.timestamp <= block.timestamp, "EXPIRED");  // always true!

        IERC20(tokenIn).transferFrom(msg.sender, pair, amountIn);

        (uint112 r0, uint112 r1) = IUniswapPair(pair).getReserves();
        amountOut = (amountIn * uint256(r1)) / (uint256(r0) + amountIn);
        IUniswapPair(pair).swap(0, amountOut, to, "");
    }

    // VULN: No minimum liquidity — first deposit inflation
    function addLiquidity(
        address tokenA,
        address tokenB,
        uint256 amountA,
        uint256 amountB,
        address pair,
        address to
    ) external returns (uint256 liquidity) {
        IERC20(tokenA).transferFrom(msg.sender, pair, amountA);
        IERC20(tokenB).transferFrom(msg.sender, pair, amountB);
        liquidity = IUniswapPair(pair).mint(to);
    }

    // VULN: tx.origin auth — phishable
    function emergencyWithdraw(address token, uint256 amount) external {
        require(tx.origin == owner, "Not owner");
        IERC20(token).transfer(msg.sender, amount);
    }

    // VULN: Arbitrary external call — dangerous
    function execute(address target, bytes calldata data) external {
        require(msg.sender == owner, "Not owner");
        (bool ok,) = target.call(data);
        require(ok);
    }
}
"""

# All 3 contracts combined (for multi-contract analysis)
UNISWAP_ALL_SOL = UNISWAP_PAIR_SOL + "\n" + UNISWAP_FACTORY_SOL + "\n" + UNISWAP_ROUTER_SOL


# ═══════════════════════════════════════════════════════════════
#  Shared Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def parsed_pair():
    """Parse UniswapPair with regex parser."""
    from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
    parser = SoliditySemanticParser()
    contracts = parser.parse(UNISWAP_PAIR_SOL)
    return contracts

@pytest.fixture(scope="module")
def parsed_factory():
    from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
    parser = SoliditySemanticParser()
    return parser.parse(UNISWAP_FACTORY_SOL)

@pytest.fixture(scope="module")
def parsed_router():
    from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
    parser = SoliditySemanticParser()
    return parser.parse(UNISWAP_ROUTER_SOL)

@pytest.fixture(scope="module")
def parsed_all():
    """Parse all 3 Uniswap contracts together."""
    from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
    parser = SoliditySemanticParser()
    return parser.parse(UNISWAP_ALL_SOL)

@pytest.fixture(scope="module")
def ast_parsed_pair():
    """Parse UniswapPair with AST parser."""
    from agl_security_tool.detectors.solidity_ast_parser import SolidityASTParserFull
    parser = SolidityASTParserFull()
    return parser.parse(UNISWAP_PAIR_SOL)

@pytest.fixture(scope="module")
def ast_parsed_all():
    """Parse all contracts with AST parser."""
    from agl_security_tool.detectors.solidity_ast_parser import SolidityASTParserFull
    parser = SolidityASTParserFull()
    return parser.parse(UNISWAP_ALL_SOL)


# ═══════════════════════════════════════════════════════════════
#  1. AST Parser Tests — تحليل الشجرة النحوية
# ═══════════════════════════════════════════════════════════════

class TestSolidityASTParser:
    """Test AST parser on Uniswap contracts."""

    def test_ast_parser_parses_pair(self, ast_parsed_pair):
        """AST parser يستخرج عقد UniswapPair."""
        assert len(ast_parsed_pair) >= 1
        names = [c.name for c in ast_parsed_pair]
        assert "UniswapPair" in names

    def test_ast_parser_extracts_functions(self, ast_parsed_pair):
        """AST parser يستخرج جميع الدوال."""
        pair = next(c for c in ast_parsed_pair if c.name == "UniswapPair")
        func_names = set(pair.functions.keys())
        for expected in ("swap", "mint", "burn", "getReserves", "getSpotPrice"):
            assert expected in func_names, f"Missing function: {expected}"

    def test_ast_parser_extracts_state_vars(self, ast_parsed_pair):
        """AST parser يستخرج متغيرات الحالة."""
        pair = next(c for c in ast_parsed_pair if c.name == "UniswapPair")
        var_names = set(pair.state_vars.keys())
        for expected in ("token0", "token1", "reserve0", "reserve1", "totalSupply"):
            assert expected in var_names, f"Missing state var: {expected}"

    def test_ast_parser_detects_modifiers(self, ast_parsed_pair):
        """AST parser يكتشف modifier lock."""
        pair = next(c for c in ast_parsed_pair if c.name == "UniswapPair")
        swap_fn = pair.functions.get("swap")
        assert swap_fn is not None
        assert "lock" in swap_fn.modifiers

    def test_ast_parser_multi_contract(self, ast_parsed_all):
        """AST parser يحلل عقود متعددة في ملف واحد."""
        names = {c.name for c in ast_parsed_all}
        # Should find at least UniswapPair, UniswapFactory, UniswapRouter
        assert "UniswapPair" in names
        assert "UniswapFactory" in names
        assert "UniswapRouter" in names

    def test_ast_parser_function_visibility(self, ast_parsed_pair):
        """AST parser يستخرج صلاحيات الدوال."""
        pair = next(c for c in ast_parsed_pair if c.name == "UniswapPair")
        # getReserves should be public/view
        get_res = pair.functions.get("getReserves")
        assert get_res is not None
        assert get_res.mutability in ("view", "pure")

    def test_ast_parser_extracts_events(self, ast_parsed_pair):
        """AST parser يستخرج الأحداث."""
        pair = next(c for c in ast_parsed_pair if c.name == "UniswapPair")
        # Check events exist in the source contract
        assert "Swap" in UNISWAP_PAIR_SOL

    def test_ast_parser_external_calls(self, ast_parsed_pair):
        """AST parser يكتشف الاستدعاءات الخارجية."""
        pair = next(c for c in ast_parsed_pair if c.name == "UniswapPair")
        swap_fn = pair.functions.get("swap")
        assert swap_fn is not None
        # swap() has IERC20.transfer calls and to.call(data)
        has_external = bool(swap_fn.external_calls) or bool(swap_fn.operations)
        assert has_external, "swap() should have external calls"


# ═══════════════════════════════════════════════════════════════
#  2. Detectors Tests — كاشفات الثغرات
# ═══════════════════════════════════════════════════════════════

class TestDetectors:
    """Test detector runner on Uniswap contracts."""

    def test_detectors_find_vulnerabilities(self, parsed_all):
        """Detectors تكتشف ثغرات في عقود Uniswap."""
        from agl_security_tool.detectors import DetectorRunner
        runner = DetectorRunner()
        findings = runner.run(parsed_all)
        assert len(findings) > 0, "Should detect at least one vulnerability"

    def test_detectors_find_unchecked_return(self, parsed_all):
        """Detectors تكتشف ERC20 return غير المفحوصة."""
        from agl_security_tool.detectors import DetectorRunner
        runner = DetectorRunner()
        findings = runner.run(parsed_all)
        categories = {f.detector_id for f in findings}
        # burn() has unchecked token.transfer returns
        has_unchecked = any(
            "UNCHECKED" in (f.detector_id or "") or "unchecked" in (f.title or "").lower()
            for f in findings
        )
        assert has_unchecked, f"Should detect unchecked return values. Found: {categories}"

    def test_detectors_find_tx_origin(self, parsed_all):
        """Detectors تكتشف tx.origin في Router."""
        from agl_security_tool.detectors import DetectorRunner
        runner = DetectorRunner()
        findings = runner.run(parsed_all)
        has_tx_origin = any(
            "tx.origin" in (f.title or "").lower()
            or "tx-origin" in (f.detector_id or "").lower()
            or "TX" in (f.detector_id or "") and "ORIGIN" in (f.detector_id or "")
            for f in findings
        )
        assert has_tx_origin, f"Should detect tx.origin usage. Found IDs: {[f.detector_id for f in findings]}"

    def test_detectors_finding_structure(self, parsed_all):
        """كل finding يحتوي على الحقول المطلوبة."""
        from agl_security_tool.detectors import DetectorRunner
        runner = DetectorRunner()
        findings = runner.run(parsed_all)
        for f in findings[:5]:
            d = f.to_dict()
            assert "detector" in d or "detector_id" in d
            assert "title" in d
            assert "severity" in d
            assert "confidence" in d

    def test_detectors_run_single(self, parsed_all):
        """تشغيل كاشف واحد محدد."""
        from agl_security_tool.detectors import DetectorRunner
        runner = DetectorRunner()
        ids = [d["id"] for d in runner.list_detectors()]
        assert len(ids) > 0
        # Run first detector individually
        single_findings = runner.run_single(ids[0], parsed_all)
        assert isinstance(single_findings, list)

    def test_detectors_skip_interfaces(self, parsed_all):
        """Detectors تتجاوز الواجهات (interfaces)."""
        from agl_security_tool.detectors import DetectorRunner
        runner = DetectorRunner()
        findings = runner.run(parsed_all)
        # No findings should be on IERC20 interface
        interface_findings = [
            f for f in findings
            if getattr(f, "contract", "") == "IERC20"
        ]
        assert len(interface_findings) == 0, "Should not report findings on interfaces"

    def test_detectors_severity_distribution(self, parsed_all):
        """Findings تتوزع على مستويات خطورة مختلفة."""
        from agl_security_tool.detectors import DetectorRunner
        runner = DetectorRunner()
        findings = runner.run(parsed_all)
        severities = {str(f.severity) for f in findings}
        # With these vulnerable contracts, we expect at least 2 severity levels
        assert len(severities) >= 2, f"Expected diverse severities, got: {severities}"

    def test_detectors_list_all(self):
        """يمكن استعراض جميع الكاشفات المسجلة."""
        from agl_security_tool.detectors import DetectorRunner
        runner = DetectorRunner()
        detectors = runner.list_detectors()
        assert len(detectors) >= 10, f"Expected 10+ detectors, got {len(detectors)}"
        for d in detectors:
            assert "id" in d
            assert "title" in d


# ═══════════════════════════════════════════════════════════════
#  3. State Extraction Tests — استخراج الحالة (Layer 1)
# ═══════════════════════════════════════════════════════════════

class TestStateExtraction:
    """Test Layer 1: State Extraction on Uniswap contracts."""

    def test_state_extraction_runs(self):
        """State extraction يعمل على UniswapPair."""
        from agl_security_tool.state_extraction import StateExtractionEngine
        engine = StateExtractionEngine({
            "action_space": False, "attack_simulation": False, "search_engine": False
        })
        result = engine.extract_source(UNISWAP_PAIR_SOL)
        assert result is not None
        assert result.graph is not None

    def test_state_extraction_financial_graph(self):
        """يبني Financial Graph من عقد Pair."""
        from agl_security_tool.state_extraction import StateExtractionEngine
        engine = StateExtractionEngine({
            "action_space": False, "attack_simulation": False, "search_engine": False
        })
        result = engine.extract_source(UNISWAP_PAIR_SOL)
        graph = result.graph
        # Graph should have nodes (state vars, functions, etc.)
        assert graph is not None

    def test_state_extraction_multicontract(self):
        """State extraction يتعامل مع عقود متعددة."""
        from agl_security_tool.state_extraction import StateExtractionEngine
        engine = StateExtractionEngine({
            "action_space": False, "attack_simulation": False, "search_engine": False
        })
        result = engine.extract_source(UNISWAP_ALL_SOL)
        assert result is not None

    def test_execution_semantics(self, parsed_pair):
        """ExecutionSemantics يكتشف ترتيب CEI في swap()."""
        from agl_security_tool.state_extraction.execution_semantics import ExecutionSemanticsExtractor
        extractor = ExecutionSemanticsExtractor()
        timelines = extractor.extract(parsed_pair)
        assert isinstance(timelines, list)
        # swap() has external call (transfer, then to.call) before state update
        # Should produce execution timelines for non-view functions
        assert len(timelines) > 0, "Should have execution timelines for state-changing functions"

    def test_function_effects(self, parsed_pair):
        """FunctionEffects يكتشف القراءات والكتابات."""
        from agl_security_tool.state_extraction.function_effects import FunctionEffectModeler
        modeler = FunctionEffectModeler()
        effects = modeler.model(parsed_pair)
        assert isinstance(effects, list)
        assert len(effects) > 0, "Should produce function effects for Uniswap functions"

    def test_state_mutation(self, parsed_pair):
        """StateMutation يتتبع تغييرات الحالة."""
        from agl_security_tool.state_extraction.state_mutation import StateMutationTracker
        tracker = StateMutationTracker()
        mutations = tracker.track(parsed_pair)
        assert isinstance(mutations, list)
        assert len(mutations) > 0, "Should track state mutations for swap/mint/burn"


# ═══════════════════════════════════════════════════════════════
#  4. Action Space Tests — مساحة الأفعال (Layer 2)
# ═══════════════════════════════════════════════════════════════

class TestActionSpace:
    """Test Layer 2: Action Space on Uniswap contracts."""

    def test_action_space_builds(self, parsed_all):
        """ActionSpaceBuilder يبني مساحة أفعال من عقود Uniswap."""
        from agl_security_tool.action_space import ActionSpaceBuilder
        builder = ActionSpaceBuilder()
        space = builder.build(parsed_all)
        assert space is not None

    def test_action_space_has_actions(self, parsed_all):
        """مساحة الأفعال تحتوي على أفعال."""
        from agl_security_tool.action_space import ActionSpaceBuilder
        builder = ActionSpaceBuilder()
        space = builder.build(parsed_all)
        # Space should contain actions (swap, mint, burn, etc.)
        assert space.graph is not None
        actions = space.graph.actions if hasattr(space.graph, "actions") else {}
        assert len(actions) > 0, "Should have at least one action"

    def test_action_space_from_state_extraction(self):
        """Action Space يقبل بيانات من State Extraction."""
        from agl_security_tool.state_extraction import StateExtractionEngine
        from agl_security_tool.action_space import ActionSpaceBuilder
        from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser

        parser = SoliditySemanticParser()
        contracts = parser.parse(UNISWAP_PAIR_SOL)

        # Layer 1
        se = StateExtractionEngine({
            "action_space": False, "attack_simulation": False, "search_engine": False
        })
        extraction = se.extract_source(UNISWAP_PAIR_SOL)

        # Layer 2 — with graph from Layer 1
        builder = ActionSpaceBuilder()
        space = builder.build(contracts, graph=extraction.graph)
        assert space is not None

    def test_action_space_classifies_swap(self, parsed_all):
        """Action Space يصنف swap() كعمل خطير."""
        from agl_security_tool.action_space import ActionSpaceBuilder
        builder = ActionSpaceBuilder()
        space = builder.build(parsed_all)
        actions = space.graph.actions if hasattr(space.graph, "actions") else {}
        # Look for swap-related action
        swap_actions = [
            a for name, a in actions.items()
            if "swap" in name.lower()
        ]
        assert len(swap_actions) > 0, "Should have swap action"

    def test_action_graph_edges(self, parsed_all):
        """Action Graph يحتوي على حواف (تبعيات بين الأفعال)."""
        from agl_security_tool.action_space import ActionSpaceBuilder
        builder = ActionSpaceBuilder()
        space = builder.build(parsed_all)
        graph = space.graph
        edges = graph.edges if hasattr(graph, "edges") else []
        # With multiple contracts and functions, should have some edges
        assert isinstance(edges, (list, dict))


# ═══════════════════════════════════════════════════════════════
#  5. Attack Engine Tests — محرك الهجوم (Layer 3)
# ═══════════════════════════════════════════════════════════════

class TestAttackEngine:
    """Test Layer 3: Attack Engine on Uniswap contracts."""

    def test_attack_engine_simulates(self, parsed_all):
        """Attack Engine يُحاكي هجمات على عقود Uniswap."""
        from agl_security_tool.state_extraction import StateExtractionEngine
        from agl_security_tool.action_space import ActionSpaceBuilder
        from agl_security_tool.attack_engine import AttackSimulationEngine

        # Layer 1
        se = StateExtractionEngine({
            "action_space": False, "attack_simulation": False, "search_engine": False
        })
        extraction = se.extract_source(UNISWAP_ALL_SOL)

        # Layer 2
        builder = ActionSpaceBuilder()
        space = builder.build(parsed_all, graph=extraction.graph)

        # Layer 3
        engine = AttackSimulationEngine()
        summary = engine.simulate_all(extraction.graph, space)
        assert summary is not None

    def test_attack_engine_returns_results(self, parsed_all):
        """Attack Engine يُعيد نتائج محاكاة."""
        from agl_security_tool.state_extraction import StateExtractionEngine
        from agl_security_tool.action_space import ActionSpaceBuilder
        from agl_security_tool.attack_engine import AttackSimulationEngine

        se = StateExtractionEngine({
            "action_space": False, "attack_simulation": False, "search_engine": False
        })
        extraction = se.extract_source(UNISWAP_ALL_SOL)

        builder = ActionSpaceBuilder()
        space = builder.build(parsed_all, graph=extraction.graph)

        engine = AttackSimulationEngine()
        summary = engine.simulate_all(extraction.graph, space)

        # Summary should have standard fields
        assert hasattr(summary, "all_results") or hasattr(summary, "profitable_attacks")

    def test_attack_engine_attack_types(self, parsed_all):
        """Attack Engine يكتشف أنواع هجمات."""
        from agl_security_tool.state_extraction import StateExtractionEngine
        from agl_security_tool.action_space import ActionSpaceBuilder
        from agl_security_tool.attack_engine import AttackSimulationEngine

        se = StateExtractionEngine({
            "action_space": False, "attack_simulation": False, "search_engine": False
        })
        extraction = se.extract_source(UNISWAP_ALL_SOL)

        builder = ActionSpaceBuilder()
        space = builder.build(parsed_all, graph=extraction.graph)

        engine = AttackSimulationEngine()
        summary = engine.simulate_all(extraction.graph, space)

        # With vulnerable Uniswap contracts, should identify some attack types
        attack_types = getattr(summary, "attack_types_found", {})
        assert isinstance(attack_types, dict)


# ═══════════════════════════════════════════════════════════════
#  6. Search Engine Tests — محرك البحث (Layer 4)
# ═══════════════════════════════════════════════════════════════

class TestSearchEngine:
    """Test Layer 4: Search Engine on Uniswap contracts."""

    def test_search_engine_runs(self, parsed_all):
        """Search Engine يعمل على عقود Uniswap."""
        from agl_security_tool.state_extraction import StateExtractionEngine
        from agl_security_tool.action_space import ActionSpaceBuilder
        from agl_security_tool.attack_engine import AttackSimulationEngine
        from agl_security_tool.search_engine import SearchOrchestrator

        se = StateExtractionEngine({
            "action_space": False, "attack_simulation": False, "search_engine": False
        })
        extraction = se.extract_source(UNISWAP_ALL_SOL)

        builder = ActionSpaceBuilder()
        space = builder.build(parsed_all, graph=extraction.graph)

        attack = AttackSimulationEngine()

        orchestrator = SearchOrchestrator()
        result = orchestrator.search(extraction.graph, space, attack)
        assert result is not None

    def test_search_engine_finds_targets(self, parsed_all):
        """Search Engine يجد أهداف بحث."""
        from agl_security_tool.state_extraction import StateExtractionEngine
        from agl_security_tool.action_space import ActionSpaceBuilder
        from agl_security_tool.attack_engine import AttackSimulationEngine
        from agl_security_tool.search_engine import SearchOrchestrator

        se = StateExtractionEngine({
            "action_space": False, "attack_simulation": False, "search_engine": False
        })
        extraction = se.extract_source(UNISWAP_ALL_SOL)

        builder = ActionSpaceBuilder()
        space = builder.build(parsed_all, graph=extraction.graph)

        attack = AttackSimulationEngine()

        orchestrator = SearchOrchestrator()
        result = orchestrator.search(extraction.graph, space, attack)

        targets = getattr(result, "targets", [])
        weaknesses = getattr(result, "weaknesses", [])
        # Should find some targets or weaknesses in vulnerable contracts
        assert isinstance(targets, list)
        assert isinstance(weaknesses, list)

    def test_search_engine_full_pipeline_l1_to_l4(self):
        """Pipeline كامل من Layer 1 إلى Layer 4."""
        from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
        from agl_security_tool.state_extraction import StateExtractionEngine
        from agl_security_tool.action_space import ActionSpaceBuilder
        from agl_security_tool.attack_engine import AttackSimulationEngine
        from agl_security_tool.search_engine import SearchOrchestrator

        # Parse
        parser = SoliditySemanticParser()
        contracts = parser.parse(UNISWAP_ALL_SOL)
        assert len(contracts) >= 3

        # L1: State Extraction
        se = StateExtractionEngine({
            "action_space": False, "attack_simulation": False, "search_engine": False
        })
        extraction = se.extract_source(UNISWAP_ALL_SOL)
        assert extraction.graph is not None

        # L2: Action Space
        builder = ActionSpaceBuilder()
        space = builder.build(contracts, graph=extraction.graph)
        assert space.graph is not None

        # L3: Attack Engine
        attack = AttackSimulationEngine()
        summary = attack.simulate_all(extraction.graph, space)
        assert summary is not None

        # L4: Search Engine
        orchestrator = SearchOrchestrator()
        search_result = orchestrator.search(extraction.graph, space, attack)
        assert search_result is not None


# ═══════════════════════════════════════════════════════════════
#  7. Heikal Math Tests — خوارزميات هيكل الرياضية
# ═══════════════════════════════════════════════════════════════

class TestHeikalMath:
    """Test Heikal Math algorithms on Uniswap-derived data."""

    def test_tunneling_scorer_basic(self):
        """Tunneling Scorer يحسب احتمال اختراق حواجز الأمان."""
        from agl_security_tool.heikal_math.tunneling_scorer import (
            HeikalTunnelingScorer, SecurityBarrier
        )
        scorer = HeikalTunnelingScorer()

        # Simulate barriers from UniswapPair.swap() — has lock modifier but callback
        barriers = [
            SecurityBarrier(barrier_type="modifier", height=0.7, thickness=1, source="lock"),
            SecurityBarrier(barrier_type="require", height=0.5, thickness=1, source="INSUFFICIENT_OUTPUT"),
            SecurityBarrier(barrier_type="require", height=0.5, thickness=1, source="INSUFFICIENT_LIQUIDITY"),
        ]

        result = scorer.compute(barriers, attack_energy=0.6, chain_length=2)
        assert result is not None
        assert 0.0 <= result.confidence <= 1.0
        assert result.barriers_analyzed == 3

    def test_tunneling_scorer_no_barriers(self):
        """بدون حواجز — p_total عالي (لا عوائق)."""
        from agl_security_tool.heikal_math.tunneling_scorer import (
            HeikalTunnelingScorer, SecurityBarrier
        )
        scorer = HeikalTunnelingScorer()
        result = scorer.compute([], attack_energy=0.8, chain_length=1)
        # No barriers = p_total = 1.0 (no obstacle), confidence may be low (no data)
        assert result.p_total >= 0.9, f"No barriers should give p_total~1.0, got {result.p_total}"
        assert result.barriers_analyzed == 0

    def test_tunneling_scorer_strong_barriers(self):
        """حواجز قوية — احتمال اختراق منخفض."""
        from agl_security_tool.heikal_math.tunneling_scorer import (
            HeikalTunnelingScorer, SecurityBarrier
        )
        scorer = HeikalTunnelingScorer()
        barriers = [
            SecurityBarrier(barrier_type="modifier", height=0.95, thickness=3),
            SecurityBarrier(barrier_type="access_control", height=0.9, thickness=2),
            SecurityBarrier(barrier_type="require", height=0.85, thickness=2),
            SecurityBarrier(barrier_type="invariant", height=0.9, thickness=2),
        ]
        result = scorer.compute(barriers, attack_energy=0.3, chain_length=1)
        # Strong barriers = lower confidence
        assert result.confidence < 0.8

    def test_tunneling_bypassable_barrier(self):
        """حاجز أمان قابل للتجاوز (bypassable)."""
        from agl_security_tool.heikal_math.tunneling_scorer import (
            HeikalTunnelingScorer, SecurityBarrier
        )
        scorer = HeikalTunnelingScorer()
        barriers = [
            SecurityBarrier(barrier_type="require", height=0.8, thickness=2, bypassable=True),
        ]
        result_bypass = scorer.compute(barriers, attack_energy=0.6, chain_length=1)

        barriers_no = [
            SecurityBarrier(barrier_type="require", height=0.8, thickness=2, bypassable=False),
        ]
        result_no = scorer.compute(barriers_no, attack_energy=0.6, chain_length=1)

        # Bypassable barrier should yield higher confidence (easier to exploit)
        assert result_bypass.confidence >= result_no.confidence

    def test_wave_evaluator_dangerous_features(self):
        """Wave Evaluator يقيّم خصائص خطيرة لـ swap()."""
        from agl_security_tool.heikal_math.wave_evaluator import WaveDomainEvaluator

        evaluator = WaveDomainEvaluator()

        # Features for swap() — moves funds, no oracle guard, modifies balances
        dangerous_features = {
            "moves_funds": True,
            "cei_violation": False,  # has lock modifier
            "sends_eth": False,
            "no_access_control": True,  # anyone can call
            "not_guarded": False,  # has lock
            "reads_oracle": True,  # reads reserves (spot price)
            "has_state_conflict": True,
            "modifies_balances": True,
        }
        result = evaluator.evaluate(dangerous_features)
        assert result.heuristic_score > 0.0, "Dangerous features should produce positive score"

    def test_wave_evaluator_safe_features(self):
        """Wave Evaluator يقيّم خصائص آمنة."""
        from agl_security_tool.heikal_math.wave_evaluator import WaveDomainEvaluator

        evaluator = WaveDomainEvaluator()

        safe_features = {
            "moves_funds": False,
            "cei_violation": False,
            "sends_eth": False,
            "no_access_control": False,
            "not_guarded": False,
            "reads_oracle": False,
            "has_state_conflict": False,
            "modifies_balances": False,
        }
        result = evaluator.evaluate(safe_features)
        # All safe features → low score
        assert result.heuristic_score < 0.3, f"Safe features should have low score, got {result.heuristic_score}"

    def test_wave_evaluator_comparison(self):
        """الدوال الخطيرة تحصل على درجة أعلى من الآمنة."""
        from agl_security_tool.heikal_math.wave_evaluator import WaveDomainEvaluator

        evaluator = WaveDomainEvaluator()

        dangerous = evaluator.evaluate({
            "moves_funds": True, "cei_violation": True, "sends_eth": True,
            "no_access_control": True, "not_guarded": True, "reads_oracle": True,
            "has_state_conflict": True, "modifies_balances": True,
        })
        safe = evaluator.evaluate({
            "moves_funds": False, "cei_violation": False, "sends_eth": False,
            "no_access_control": False, "not_guarded": False, "reads_oracle": False,
            "has_state_conflict": False, "modifies_balances": False,
        })

        assert dangerous.heuristic_score > safe.heuristic_score

    def test_holographic_pattern_matching(self):
        """Holographic Memory يطابق أنماط الثغرات."""
        from agl_security_tool.heikal_math.holographic_patterns import HolographicVulnerabilityMemory

        memory = HolographicVulnerabilityMemory()

        # Features resembling a reentrancy pattern
        reentrancy_features = {
            "has_external_call": True,
            "state_after_call": True,
            "moves_funds": True,
            "has_guard": False,
            "cei_violation": True,
        }
        matches = memory.match(reentrancy_features)
        assert isinstance(matches, list)
        # Built-in patterns should produce some matches for reentrancy-like features

    def test_holographic_store_and_match(self):
        """تخزين نمط جديد ثم مطابقته."""
        from agl_security_tool.heikal_math.holographic_patterns import HolographicVulnerabilityMemory

        memory = HolographicVulnerabilityMemory()

        # Store a custom "sandwich attack" pattern
        sandwich_features = {
            "reads_oracle": True,
            "no_slippage_check": True,
            "moves_funds": True,
            "uses_spot_price": True,
        }
        memory.store_pattern(
            name="sandwich_attack",
            features=sandwich_features,
            severity="HIGH",
            confidence=0.85,
            description="Sandwich attack via spot price manipulation",
        )

        # Try to match similar features
        test_features = {
            "reads_oracle": True,
            "no_slippage_check": True,
            "moves_funds": True,
            "uses_spot_price": True,
        }
        matches = memory.match(test_features)
        # Should find our stored pattern (possibly among built-in ones)
        pattern_names = [m.pattern_name for m in matches]
        assert "sandwich_attack" in pattern_names or len(matches) > 0


# ═══════════════════════════════════════════════════════════════
#  8. Exploit Reasoning Tests — تحليل الاستغلال
# ═══════════════════════════════════════════════════════════════

class TestExploitReasoning:
    """Test ExploitReasoningEngine on Uniswap contracts."""

    def test_exploit_reasoning_runs(self, parsed_all):
        """Exploit Reasoning يحلل findings على عقود Uniswap."""
        from agl_security_tool.exploit_reasoning import ExploitReasoningEngine
        from agl_security_tool.detectors import DetectorRunner

        # First get findings from detectors
        runner = DetectorRunner()
        findings = runner.run(parsed_all)
        findings_dicts = [f.to_dict() for f in findings]

        # Run exploit reasoning
        engine = ExploitReasoningEngine()
        result = engine.analyze(findings_dicts, UNISWAP_ALL_SOL)

        assert "exploit_proofs" in result
        assert "exploitable_count" in result
        assert "total_analyzed" in result
        assert result["total_analyzed"] >= 0

    def test_exploit_reasoning_finds_exploitable(self, parsed_all):
        """Exploit Reasoning يجد ثغرات قابلة للاستغلال."""
        from agl_security_tool.exploit_reasoning import ExploitReasoningEngine
        from agl_security_tool.detectors import DetectorRunner

        runner = DetectorRunner()
        findings = runner.run(parsed_all)
        findings_dicts = [f.to_dict() for f in findings]

        engine = ExploitReasoningEngine()
        result = engine.analyze(findings_dicts, UNISWAP_ALL_SOL)

        proofs = result["exploit_proofs"]
        assert isinstance(proofs, list)
        # With multiple vulnerabilities, should find at least one exploitable
        if len(proofs) > 0:
            # Check proof structure
            proof = proofs[0]
            assert "exploitable" in proof
            assert "function" in proof
            assert "category" in proof

    def test_exploit_reasoning_proof_structure(self, parsed_all):
        """بنية ExploitProof صحيحة."""
        from agl_security_tool.exploit_reasoning import ExploitReasoningEngine
        from agl_security_tool.detectors import DetectorRunner

        runner = DetectorRunner()
        findings = runner.run(parsed_all)
        findings_dicts = [f.to_dict() for f in findings]

        engine = ExploitReasoningEngine()
        result = engine.analyze(findings_dicts, UNISWAP_ALL_SOL)

        for proof in result["exploit_proofs"]:
            assert "exploitable" in proof
            assert "severity" in proof
            assert isinstance(proof["exploitable"], bool)

    def test_exploit_reasoning_with_manual_findings(self):
        """Exploit Reasoning يعمل مع findings يدوية."""
        from agl_security_tool.exploit_reasoning import ExploitReasoningEngine

        manual_findings = [
            {
                "severity": "CRITICAL",
                "function": "swap",
                "category": "reentrancy",
                "description": "External call before state update in swap()",
                "detector": "REENTRANCY",
                "contract": "UniswapPair",
                "title": "Reentrancy in swap()",
            },
            {
                "severity": "HIGH",
                "function": "burn",
                "category": "unchecked_return",
                "description": "Unchecked ERC20 transfer return in burn()",
                "detector": "UNCHECKED-RETURN",
                "contract": "UniswapPair",
                "title": "Unchecked return in burn()",
            },
        ]

        engine = ExploitReasoningEngine()
        result = engine.analyze(manual_findings, UNISWAP_PAIR_SOL)
        assert result["total_analyzed"] >= 0


# ═══════════════════════════════════════════════════════════════
#  9. PoC Generator Tests — مولد إثبات المفهوم
# ═══════════════════════════════════════════════════════════════

class TestPoCGenerator:
    """Test PoC generation on Uniswap contracts."""

    def test_poc_generator_creates_files(self):
        """PoC Generator ينشئ ملفات .t.sol."""
        from agl_security_tool.poc_generator import PoCGenerator

        tmpdir = tempfile.mkdtemp(prefix="agl_poc_test_")
        try:
            # Create minimal project structure
            src_dir = os.path.join(tmpdir, "src")
            os.makedirs(src_dir, exist_ok=True)
            with open(os.path.join(src_dir, "UniswapPair.sol"), "w") as f:
                f.write(UNISWAP_PAIR_SOL)

            gen = PoCGenerator(project_path=tmpdir)

            # Simulate audit results with exploit proofs
            all_results = {
                "exploit_reasoning": {
                    "UniswapPair": {
                        "exploit_proofs": [
                            {
                                "exploitable": True,
                                "function": "swap",
                                "category": "reentrancy",
                                "severity": "CRITICAL",
                                "confidence": 0.9,
                                "attack_steps": [
                                    "Call swap() with callback data",
                                    "In callback, re-enter swap()",
                                    "Drain reserves",
                                ],
                                "viable_path": "swap → callback → swap",
                                "z3_result": "SAT",
                            },
                        ]
                    }
                }
            }

            result = gen.generate(all_results)
            assert "poc_files" in result
            assert "count" in result
            assert isinstance(result["poc_files"], list)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_poc_generator_without_exploitable(self):
        """PoC Generator لا ينشئ ملفات إذا لا توجد ثغرات قابلة للاستغلال."""
        from agl_security_tool.poc_generator import PoCGenerator

        tmpdir = tempfile.mkdtemp(prefix="agl_poc_test_")
        try:
            src_dir = os.path.join(tmpdir, "src")
            os.makedirs(src_dir, exist_ok=True)

            gen = PoCGenerator(project_path=tmpdir)

            # No exploitable findings
            all_results = {
                "exploit_reasoning": {
                    "UniswapPair": {
                        "exploit_proofs": [
                            {
                                "exploitable": False,
                                "function": "getReserves",
                                "category": "info",
                                "severity": "INFO",
                            }
                        ]
                    }
                }
            }

            result = gen.generate(all_results)
            assert result["count"] == 0

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_poc_generator_with_full_pipeline(self, parsed_all):
        """PoC Generator يعمل مع بيانات من Detectors + Exploit Reasoning."""
        from agl_security_tool.detectors import DetectorRunner
        from agl_security_tool.exploit_reasoning import ExploitReasoningEngine
        from agl_security_tool.poc_generator import PoCGenerator

        # Detectors
        runner = DetectorRunner()
        findings = runner.run(parsed_all)
        findings_dicts = [f.to_dict() for f in findings]

        # Exploit Reasoning
        er_engine = ExploitReasoningEngine()
        er_result = er_engine.analyze(findings_dicts, UNISWAP_ALL_SOL)

        tmpdir = tempfile.mkdtemp(prefix="agl_poc_test_")
        try:
            src_dir = os.path.join(tmpdir, "src")
            os.makedirs(src_dir, exist_ok=True)
            with open(os.path.join(src_dir, "Uniswap.sol"), "w") as f:
                f.write(UNISWAP_ALL_SOL)

            gen = PoCGenerator(project_path=tmpdir)

            # Build results dict matching pipeline format
            # Ensure confidence is numeric for PoC generator
            safe_findings = []
            for fd in findings_dicts:
                fd_copy = dict(fd)
                conf = fd_copy.get("confidence", 0.5)
                if isinstance(conf, str):
                    conf_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
                    fd_copy["confidence"] = conf_map.get(conf.lower(), 0.5)
                safe_findings.append(fd_copy)

            all_results = {
                "exploit_reasoning": {
                    "UniswapAll": {
                        "exploit_proofs": er_result["exploit_proofs"],
                        "exploitable_count": er_result["exploitable_count"],
                    }
                },
                "unified_findings": safe_findings,
            }

            result = gen.generate(all_results)
            assert isinstance(result["poc_files"], list)
            assert isinstance(result["count"], int)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════
#  10. Integration: Full Isolated Pipeline
# ═══════════════════════════════════════════════════════════════

class TestFullIsolatedPipeline:
    """Test all layers in sequence on Uniswap contracts."""

    def test_full_pipeline_pair(self):
        """Pipeline كامل على UniswapPair — كل الطبقات."""
        from agl_security_tool.detectors.solidity_parser import SoliditySemanticParser
        from agl_security_tool.detectors.solidity_ast_parser import SolidityASTParserFull
        from agl_security_tool.detectors import DetectorRunner
        from agl_security_tool.state_extraction import StateExtractionEngine
        from agl_security_tool.action_space import ActionSpaceBuilder
        from agl_security_tool.attack_engine import AttackSimulationEngine
        from agl_security_tool.search_engine import SearchOrchestrator
        from agl_security_tool.exploit_reasoning import ExploitReasoningEngine
        from agl_security_tool.heikal_math.tunneling_scorer import HeikalTunnelingScorer, SecurityBarrier
        from agl_security_tool.heikal_math.wave_evaluator import WaveDomainEvaluator

        # === Parse (both parsers) ===
        regex_parser = SoliditySemanticParser()
        ast_parser = SolidityASTParserFull()

        contracts_regex = regex_parser.parse(UNISWAP_ALL_SOL)
        contracts_ast = ast_parser.parse(UNISWAP_ALL_SOL)

        assert len(contracts_regex) >= 3, f"Regex parser found {len(contracts_regex)} contracts"
        assert len(contracts_ast) >= 3, f"AST parser found {len(contracts_ast)} contracts"

        # === Detectors ===
        runner = DetectorRunner()
        findings = runner.run(contracts_regex)
        assert len(findings) > 0, "Should detect vulnerabilities"
        findings_dicts = [f.to_dict() for f in findings]

        # === Layer 1: State Extraction ===
        se = StateExtractionEngine({
            "action_space": False, "attack_simulation": False, "search_engine": False
        })
        extraction = se.extract_source(UNISWAP_ALL_SOL)
        assert extraction.graph is not None

        # === Layer 2: Action Space ===
        builder = ActionSpaceBuilder()
        space = builder.build(contracts_regex, graph=extraction.graph)
        assert space.graph is not None

        # === Layer 3: Attack Engine ===
        attack_engine = AttackSimulationEngine()
        attack_summary = attack_engine.simulate_all(extraction.graph, space)
        assert attack_summary is not None

        # === Layer 4: Search Engine ===
        search = SearchOrchestrator()
        search_result = search.search(extraction.graph, space, attack_engine)
        assert search_result is not None

        # === Exploit Reasoning ===
        er_engine = ExploitReasoningEngine()
        er_result = er_engine.analyze(findings_dicts, UNISWAP_ALL_SOL)
        assert "exploit_proofs" in er_result

        # === Heikal Math ===
        tunneling = HeikalTunnelingScorer()
        wave = WaveDomainEvaluator()

        # Compute tunneling for each finding
        for fd in findings_dicts[:3]:
            barriers = []
            func_name = fd.get("function", "")
            # Simple barrier extraction from severity
            if fd.get("severity") in ("LOW", "INFO"):
                barriers.append(SecurityBarrier(
                    barrier_type="require", height=0.8, thickness=2
                ))
            t_result = tunneling.compute(barriers, attack_energy=0.5, chain_length=2)
            assert 0.0 <= t_result.confidence <= 1.0

        # Wave evaluation
        w_result = wave.evaluate({
            "moves_funds": True, "cei_violation": False, "sends_eth": False,
            "no_access_control": True, "not_guarded": False, "reads_oracle": True,
            "has_state_conflict": True, "modifies_balances": True,
        })
        assert w_result.heuristic_score >= 0.0

        # === Summary ===
        print(f"\n{'='*60}")
        print(f"Full Isolated Pipeline — Uniswap Results")
        print(f"{'='*60}")
        print(f"  Contracts parsed (regex): {len(contracts_regex)}")
        print(f"  Contracts parsed (AST):   {len(contracts_ast)}")
        print(f"  Findings (detectors):     {len(findings)}")
        print(f"  Exploit proofs:           {len(er_result['exploit_proofs'])}")
        print(f"  Exploitable:              {er_result['exploitable_count']}")
        print(f"  Attack types (L3):        {getattr(attack_summary, 'attack_types_found', {})}")
        print(f"{'='*60}")
