"""
AGL Security — أداة تحليل أمان العقود الذكية
Smart Contract Security Analysis Tool

Usage:
    from agl_security_tool import AGLSecurityAudit
    audit = AGLSecurityAudit()
    result = audit.scan("path/to/contract.sol")

    # Unified Risk Scoring
    from agl_security_tool.risk_core import RiskCore
    rc = RiskCore()
    breakdown = rc.compute_exploit_probability(formal=0.9, heuristic=0.6, profit=0.3, exploit_proven=True)

    # Native Tool Backends (self-contained Slither/Mythril/Semgrep)
    from agl_security_tool.tool_backends import ToolBackendRunner
    runner = ToolBackendRunner()
    result = runner.analyze("contract.sol")

    # Benchmark Evaluation
    from agl_security_tool.benchmark_runner import BenchmarkRunner

    # Weight Optimization (automatic logistic regression)
    from agl_security_tool.weight_optimizer import WeightOptimizer

    # On-Chain Context (optional, requires AGL_RPC_URL)
    from agl_security_tool.onchain_context import OnChainContext

    # State Extraction Engine — Layer 1
    from agl_security_tool.state_extraction import StateExtractionEngine
    engine = StateExtractionEngine()
    graph = engine.extract("path/to/contract.sol")
    # Contract-Level Intelligence (Phase 2 — Noisy-OR + Meta)
    from agl_security_tool.contract_intelligence import (
        ContractAggregator, ContractMetrics, MetaClassifier
    )
"""

__version__ = "2.1.0"
__author__ = "AGL Team"

from .core import AGLSecurityAudit
from .project_scanner import ProjectScanner
from .risk_core import RiskCore, RiskBreakdown
from .tool_backends import (
    ToolBackendRunner,
    SlitherRunner,
    MythrilRunner,
    SemgrepRunner,
)
from .benchmark_runner import BenchmarkRunner, CalibrationResult, CalibrationBin
from .weight_optimizer import WeightOptimizer, TrainingConfig, TrainingResult
from .onchain_context import OnChainContext
from .contract_intelligence import (
    ContractAggregator,
    ContractMetrics,
    MetaClassifier,
    ContractVerdict,
    ContractCalibrationResult,
)
from .poc_generator import PoCGenerator

__all__ = [
    "AGLSecurityAudit",
    "ProjectScanner",
    "RiskCore",
    "RiskBreakdown",
    "ToolBackendRunner",
    "SlitherRunner",
    "MythrilRunner",
    "SemgrepRunner",
    "BenchmarkRunner",
    "CalibrationResult",
    "CalibrationBin",
    "WeightOptimizer",
    "TrainingConfig",
    "TrainingResult",
    "OnChainContext",
    "ContractAggregator",
    "ContractMetrics",
    "MetaClassifier",
    "ContractVerdict",
    "ContractCalibrationResult",
    "PoCGenerator",
    "__version__",
]
