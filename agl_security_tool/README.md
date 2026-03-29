# AGL Security Tool

> **أداة تحليل أمان العقود الذكية — Smart Contract Security Analysis Tool**
>
> Version 2.1.0

---

## Overview | نظرة عامة

**English:**
AGL Security Tool is an **8-layer** smart contract security analyzer. It combines Solidity flattening, Z3 symbolic execution, financial state extraction, action space enumeration, attack simulation, 5-strategy guided search (Beam/MCTS/Evolutionary/Greedy/Hybrid), 22 semantic detectors, exploit reasoning with Z3 proofs, physics-inspired Heikal math scoring, probabilistic risk modeling, dynamic PoC generation, and optional LLM enrichment — plus integration with Slither, Mythril, Semgrep, and an offensive security engine when available.

**العربية:**
أداة AGL Security هي محلل أمان **بـ 8 طبقات** للعقود الذكية. تجمع بين: تسطيح Solidity، تنفيذ رمزي Z3، استخراج الحالة المالية، تعداد فضاء الأفعال، محاكاة الهجمات الاقتصادية، بحث ذكي بـ 5 استراتيجيات (Beam/MCTS/تطوري/جشع/هجين)، 22 كاشفاً دلالياً، إثبات الاستغلال بـ Z3 SAT، خوارزميات هيكل الرياضية (موجة + نفق كمومي + هولوغرام + رنين)، نموذج احتمالي للمخاطر، توليد PoC ديناميكي، وإثراء اختياري بالنموذج اللغوي — مع دعم Slither و Mythril و Semgrep ومحرك الأمن الهجومي عند توفرها.

---

## Quick Start | البداية السريعة

### Python API

```python
from agl_security_tool import AGLSecurityAudit

audit = AGLSecurityAudit()
result = audit.scan("path/to/contract.sol")

# Quick scan — فحص سريع (patterns only)
result = audit.quick_scan("contract.sol")

# Deep scan — فحص عميق (Z3 + EVM + full pipeline)
result = audit.deep_scan("contract.sol")
```

### CLI — سطر الأوامر

```bash
# Standard scan — فحص قياسي
python -m agl_security_tool scan contract.sol

# Quick scan — فحص سريع
python -m agl_security_tool quick contract.sol

# Deep scan — فحص عميق
python -m agl_security_tool deep contract.sol

# Scan directory — فحص مجلد كامل
python -m agl_security_tool scan contracts/ --recursive

# Scan full project (Foundry / Hardhat / Truffle)
python -m agl_security_tool project ./my-defi-project

# Deep project scan + Markdown report
python -m agl_security_tool project ./project -m deep -f markdown -o report.md

# Project info (no scan) — معلومات المشروع
python -m agl_security_tool info ./my-project

# Dependency graph — رسم التبعيات
python -m agl_security_tool graph ./my-project -o deps.json
```

### State Extraction Engine — محرك استخراج الحالة (Layer 1)

```python
from agl_security_tool.state_extraction import StateExtractionEngine

engine = StateExtractionEngine()
result = engine.extract("path/to/contract.sol")
# result.graph contains the full financial state graph
```

### Full Project Audit Pipeline — خط الأنابيب الكامل (11 مرحلة)

```python
from agl_security_tool.audit_pipeline import run_audit

# Audit a local project (Foundry/Hardhat/Truffle/Bare)
result = run_audit("./my-defi-project", mode="deep", output_format="json")

# Audit a GitHub repo directly
result = run_audit("https://github.com/Org/repo", mode="deep")

# Audit a single .sol file
result = run_audit("contract.sol", mode="deep", skip_heikal=True)

# Generate Markdown report
result = run_audit("./project", output_format="markdown", output_path="report.md")

# With PoC generation + Foundry execution
result = run_audit("./project", generate_poc=True, run_poc=True)
```

---

## Architecture | البنية المعمارية

The tool operates as an **8-layer pipeline** (Layers 0–7). Each layer feeds the next:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGL Security Tool Pipeline                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 0: Preprocessing                                         │
│  ┌─────────────────────┐  ┌──────────────────────┐              │
│  │ SolidityFlattener   │  │ Z3SymbolicEngine     │              │
│  │ Import resolver +   │  │ 8 symbolic checks    │              │
│  │ Inheritance chain   │  │ (overflow, access...) │              │
│  └────────┬────────────┘  └──────────┬───────────┘              │
│           │                          │                          │
│  Layer 1: State Extraction ──────────┤                          │
│  ┌────────▼──────────────────────────▼───────────┐              │
│  │ StateExtractionEngine                         │              │
│  │ Entity Extraction → Relationship Mapping →    │              │
│  │ Fund Mapping → Financial Graph → Temporal     │              │
│  │ Analysis → State Mutations → Function Effects │              │
│  └────────────────────┬──────────────────────────┘              │
│                       │                                         │
│  Layer 2: Action Space                                          │
│  ┌────────────────────▼──────────────────────────┐              │
│  │ ActionSpaceBuilder                            │              │
│  │ Action Enumeration → Parameter Generation →   │              │
│  │ State Linking → Attack Classification →       │              │
│  │ Action Graph                                  │              │
│  └────────────────────┬──────────────────────────┘              │
│                       │                                         │
│  Layer 3: Attack Engine                                         │
│  ┌────────────────────▼──────────────────────────┐              │
│  │ AttackSimulationEngine                        │              │
│  │ Protocol State → Action Execution →           │              │
│  │ State Mutation → Economic Events →            │              │
│  │ Profit = Value(final) - Value(initial) - Gas  │              │
│  └────────────────────┬──────────────────────────┘              │
│                       │                                         │
│  Layer 4: Search Engine                                         │
│  ┌────────────────────▼──────────────────────────┐              │
│  │ SearchOrchestrator                            │              │
│  │ Heuristic Priority → Weakness Detection →     │              │
│  │ Guided Search (Beam/MCTS/Evolutionary) →      │              │
│  │ Profit Gradient Optimization                  │              │
│  └────────────────────┬──────────────────────────┘              │
│                       │                                         │
│  Layer 5: Detectors                                             │
│  ┌────────────────────▼──────────────────────────┐              │
│  │ DetectorRunner — 22 Semantic Detectors        │              │
│  │ reentrancy (5) │ access_control (5) │         │              │
│  │ defi (4) │ token (4) │ common (4)   │         │              │
│  └────────────────────┬──────────────────────────┘              │
│                       │                                         │
│  Layer 6: Exploit Reasoning                                     │
│  ┌────────────────────▼──────────────────────────┐              │
│  │ ExploitReasoningEngine                        │              │
│  │ PathExtractor → Z3 SAT → InvariantChecker →   │              │
│  │ ExploitAssembler → RiskCore P(exploit)        │              │
│  └────────────────────┬──────────────────────────┘              │
│                       │                                         │
│  Layer 7: Heikal Math (Optional)                                │
│  ┌────────────────────▼──────────────────────────┐              │
│  │ HeikalTunnelingScorer │ WaveDomainEvaluator   │              │
│  │ HolographicVulnMemory │ ResonanceOptimizer    │              │
│  └────────────────────┬──────────────────────────┘              │
│                       │                                         │
│  Output: Dedup → RiskCore → PoC → LLM → Report                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

> For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md) (Arabic).

---

## File Structure | هيكل الملفات

```
agl_security_tool/
├── __init__.py              # Package entry — exports AGLSecurityAudit, ProjectScanner
├── __main__.py              # CLI interface (scan, quick, deep, project, info, graph)
├── core.py                  # Main AGLSecurityAudit class — orchestrates all layers
├── project_scanner.py       # Full project scanner (Foundry/Hardhat/Truffle)
├── solidity_flattener.py    # Import resolver + inheritance chain builder
├── z3_symbolic_engine.py    # Z3-based symbolic execution (8 check types)
├── exploit_reasoning.py     # Attack chain reasoning engine
├── vscode_bridge.py         # VS Code extension communication (stdin/stdout JSON)
│
├── state_extraction/        # Layer 1 — Financial state extraction
│   ├── engine.py            # StateExtractionEngine (main orchestrator)
│   ├── entity_extractor.py  # Extract tokens, pools, balances, debt, governance
│   ├── relationship_mapper.py # Access control, fund flow, oracle links
│   ├── fund_mapper.py       # Balance mapping per account/contract
│   ├── financial_graph.py   # Dynamic financial graph
│   ├── execution_semantics.py # Operation ordering + CEI violation detection
│   ├── state_mutation.py    # State(t+1) = State(t) + Σ(deltas)
│   ├── function_effects.py  # ΔState = f(inputs) with cross-function deps
│   ├── temporal_graph.py    # Temporal dependency graph
│   ├── validator.py         # Balance consistency + cycle detection
│   └── models.py            # Data models
│
├── action_space/            # Layer 2 — Attack space builder
│   ├── builder.py           # ActionSpaceBuilder (main orchestrator)
│   ├── action_enumerator.py # Extract all possible actions
│   ├── parameter_generator.py # Generate strategic parameter variants
│   ├── state_linker.py      # Link actions to ΔState effects
│   ├── action_classifier.py # Classify by attack type + severity
│   ├── action_graph.py      # Dependency graph: Nodes=Actions, Edges=Deps
│   └── models.py            # Data models
│
├── attack_engine/           # Layer 3 — Economic physics engine
│   ├── engine.py            # AttackSimulationEngine (main orchestrator)
│   ├── protocol_state.py    # Protocol state loader
│   ├── action_executor.py   # Semantic action executor
│   ├── state_mutator.py     # State transformer + rollback
│   ├── economic_engine.py   # Economic event engine (flash loans, swaps, fees)
│   ├── profit_calculator.py # Profit = Value(final) - Value(initial) - Gas - Fees
│   └── models.py            # Data models
│
├── search_engine/           # Layer 4 — Intelligent economic search
│   ├── engine.py            # SearchOrchestrator (main orchestrator)
│   ├── heuristic_prioritizer.py # Where to start searching
│   ├── weakness_detector.py # Economic weakness detection
│   ├── guided_search.py     # Beam, MCTS, Evolutionary search
│   ├── profit_gradient.py   # Parameter optimization via gradient
│   └── models.py            # Data models
│
├── detectors/               # Layer 5 — 22 semantic detectors
│   ├── __init__.py          # DetectorRunner + BaseDetector + Finding + Severity
│   ├── solidity_parser.py   # Semantic Solidity parser (no external deps)
│   ├── reentrancy.py        # 5 detectors: classic, cross-function, read-only...
│   ├── access_control.py    # 5 detectors: missing checks, centralization...
│   ├── defi.py              # 4 detectors: flash loan, oracle, MEV, governance
│   ├── token.py             # 4 detectors: ERC20 compliance, fee-on-transfer...
│   └── common.py            # 4 detectors: unchecked calls, integer issues...
│
├── heikal_math/             # Layer 7 — Physics-inspired scoring
│   ├── tunneling_scorer.py  # WKB quantum tunneling probability
│   ├── wave_evaluator.py    # Quantum wave superposition heuristic
│   ├── holographic_patterns.py # FFT-based pattern matching (numpy)
│   └── resonance_optimizer.py  # Breit-Wigner resonance optimization
│
├── audit_pipeline.py        # Project-level 11-step pipeline orchestrator
├── risk_core.py             # P(exploit) = σ(w·x + β) unified scoring
├── poc_generator.py         # Dynamic Foundry .t.sol PoC generation (9 templates)
├── contract_intelligence.py # Noisy-OR + meta-classifier aggregation
├── onchain_context.py       # On-chain data: proxy detection, 9 chains
├── tool_backends.py         # Slither/Mythril/Semgrep unified wrappers
├── benchmark_runner.py      # Evaluation vs SWC + DVDEFI ground truth
├── weight_optimizer.py      # Risk weight training via mini-batch SGD
│
├── docs/                    # Detailed documentation
│   ├── ARCHITECTURE.md      # Complete architecture reference
│   ├── AUDIT_PIPELINE_TRACE.md # All 28 functions traced
│   ├── BUGS.md              # 52 bugs: 19 fixed, 33 pending
│   └── NEGATIVE_EVIDENCE.md # Negative evidence pipeline docs
│
├── ARCHITECTURE.md              # Full architecture documentation (Arabic)
├── INTELLIGENT_SEARCH_ENGINE.md # Layer 4 deep-dive
├── state_extraction/DYNAMIC_STATE_TRANSITION_MODEL.md  # Layer 1 deep-dive
├── action_space/ACTION_SPACE_BUILDER.md                # Layer 2 deep-dive
├── attack_engine/ECONOMIC_PHYSICS_ENGINE.md            # Layer 3 deep-dive
└── heikal_math/HEIKAL_MATH_DOCUMENTATION.md            # Layer 7 deep-dive
```

---

## Dependencies | المتطلبات

### Required — مطلوبة
| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | >= 2.28.0 | HTTP communication for external APIs |
| `z3-solver` | >= 4.12.0 | Symbolic execution engine (Z3 SMT) |

### Optional — اختيارية (enhance results)
| Package | Purpose |
|---------|---------|
| `slither-analyzer` | Slither integration for additional static analysis |
| `mythril` | Mythril integration for EVM symbolic execution |
| `semgrep` | Semgrep rule-based scanning |

### Install — التثبيت

```bash
pip install -r requirements.txt
```

### Optional (enhance results) — اختيارية

```bash
pip install slither-analyzer mythril semgrep numpy
```

---

## External Engines (Optional) | المحركات الخارجية

**Important / مهم:**
This tool works **100% standalone** without any external AGL engines. However, when the full AGL project is available, `core.py` optionally imports 4 additional engines from `AGL_NextGen/src/agl/engines/`:

| Engine | Import Path | Purpose |
|--------|-------------|---------|
| `SmartContractAnalyzer` | `agl.engines.smart_contract_analyzer` | Pattern scan + Lexer + CFG (Layer 1) |
| `AGLSecuritySuite` | `agl.engines.agl_security` | Slither/Mythril wrapper (Layer 2) |
| `AGLSecurityOrchestrator` | `agl.engines.security_orchestrator` | Parallel analysis orchestration (Layer 2+) |
| `OffensiveSecurityEngine` | `agl.engines.offensive_security` | Full offensive pipeline (Layer 3) |

All 4 imports use `try/except` — if unavailable, the tool gracefully falls back to its internal engines. **No functionality is lost.**

الأداة تعمل **مستقلة 100%** بدون محركات AGL الخارجية. لكن عند توفر مشروع AGL الكامل، يستورد `core.py` اختيارياً 4 محركات من `AGL_NextGen`. كل الاستيرادات محمية بـ `try/except` — إذا لم تتوفر تعمل الأداة بمحركاتها الداخلية بدون أي خسارة.

---

## VS Code Extension | إضافة VS Code

The `agl-security-vscode/` directory contains a VS Code extension that communicates with `vscode_bridge.py` via stdin/stdout JSON protocol. This provides real-time security analysis inside VS Code.

مجلد `agl-security-vscode/` يحتوي إضافة VS Code التي تتواصل مع `vscode_bridge.py` عبر بروتوكول JSON عبر stdin/stdout.

---

## Detailed Documentation | التوثيق التفصيلي

| Document | Content |
|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Full pipeline architecture + data flow (Arabic) |
| [DYNAMIC_STATE_TRANSITION_MODEL.md](state_extraction/DYNAMIC_STATE_TRANSITION_MODEL.md) | Layer 1: State extraction math model |
| [ACTION_SPACE_BUILDER.md](action_space/ACTION_SPACE_BUILDER.md) | Layer 2: Action space construction |
| [ECONOMIC_PHYSICS_ENGINE.md](attack_engine/ECONOMIC_PHYSICS_ENGINE.md) | Layer 3: Economic physics engine |
| [INTELLIGENT_SEARCH_ENGINE.md](INTELLIGENT_SEARCH_ENGINE.md) | Layer 4: Search algorithms |

---

## License

Part of the AGL Project. See root [README.md](../README.md) for license information.
