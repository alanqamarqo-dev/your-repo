# 🛡️ AGL Security Tool

> **أداة تحليل أمان العقود الذكية — Smart Contract Security Analyzer**
>
> Version 2.1.0 | April 2026

[![CI](https://github.com/your-org/your-repo/actions/workflows/ci.yml/badge.svg?branch=agl_security)](https://github.com/your-org/your-repo/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## Overview | نظرة عامة

AGL Security Tool is an **8-layer** smart contract security analyzer combining:
- **Layer 0:** Solidity flattening + Z3 symbolic execution (BitVec 256-bit proofs)
- **Layer 1-4:** Financial state extraction → action space enumeration → attack simulation → 5-strategy guided search
- **Layer 5:** 22+ semantic vulnerability detectors
- **Layer 6:** Exploit reasoning with Z3 SAT proofs and invariant checking
- **Layer 7:** Heikal Math physics-inspired scoring (tunneling + wave + holographic + resonance)
- **Dedup + RiskCore:** Cross-layer deduplication with P(exploit) probability scoring
- **PoC Generation:** Foundry `.t.sol` proof-of-concept generation and execution

**E2E Verified** (April 2026): Full pipeline tested on real contracts — all 11 engines loaded, all 8 layers producing documented outputs, 45 unified findings with 28 exploitable proofs in 226s.

---

## Quick Start | البداية السريعة

### Install — التثبيت

```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo/agl_security_tool
pip install -e .            # Core only
pip install -e ".[api]"     # + API server
pip install -e ".[api,dev]" # + API + tests
```

### CLI — سطر الأوامر

```bash
# Standard scan — فحص قياسي
agl-security scan contract.sol

# Quick scan — فحص سريع (patterns only, seconds)
agl-security quick contract.sol

# Deep scan — فحص عميق (Z3 + all layers)
agl-security deep contract.sol

# Scan directory — فحص مجلد
agl-security scan contracts/ --recursive

# Full project scan (Foundry/Hardhat/Truffle)
agl-security project ./my-defi-project
agl-security project ./project -m deep -f markdown -o report.md
```

### Full Pipeline Audit — خط الأنابيب الكامل

```bash
# Full 8-layer audit with all engines (recommended for production audits)
agl-audit ./my-defi-project
agl-audit ./my-defi-project --mode full --format markdown -o report.md

# Audit a GitHub repo directly
agl-audit https://github.com/Uniswap/v3-core --mode full

# Skip Heikal Math (faster)
agl-audit ./project --skip-heikal

# With PoC generation + Foundry execution
agl-audit ./project --run-poc
```

### Python API

```python
from agl_security_tool import AGLSecurityAudit

audit = AGLSecurityAudit()

# Standard scan
result = audit.scan("contract.sol")

# Quick scan (patterns only)
result = audit.quick_scan("contract.sol")

# Deep scan (full pipeline)
result = audit.deep_scan("contract.sol")

# Generate report
report = audit.generate_report(result, format="markdown")
```

### Full Pipeline API

```python
from agl_security_tool.audit_pipeline import run_audit

# Full 8-layer audit on local project
result = run_audit("./my-defi-project", mode="full", output_format="json")

# Audit GitHub repo
result = run_audit("https://github.com/Org/repo", mode="deep")

# With PoC generation
result = run_audit("./project", generate_poc=True, run_poc=True)
```

### Docker — حاوية

```bash
# CLI scan (one-shot)
docker compose up agl-cli

# API server
docker compose up agl-api -d
curl http://localhost:8000/health
```

---

## Architecture | البنية المعمارية

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
│           ▼                          ▼                          │
│  Layer 1-4: State + Action + Attack + Search                    │
│  ┌──────────────────────────────────────────────────┐           │
│  │ StateExtraction → ActionSpace → AttackEngine →   │           │
│  │ SearchOrchestrator (Beam/MCTS/Evolutionary)      │           │
│  └────────────────────┬─────────────────────────────┘           │
│                       ▼                                         │
│  Layer 5: 22+ Semantic Detectors                                │
│  ┌──────────────────────────────────────────────────┐           │
│  │ reentrancy(5) │ access_control(5) │ defi(4) │    │           │
│  │ token(4) │ common(4) │ defi_advanced(2+)    │    │           │
│  └────────────────────┬─────────────────────────────┘           │
│                       ▼                                         │
│  Layer 6: Exploit Reasoning                                     │
│  ┌──────────────────────────────────────────────────┐           │
│  │ PathExtractor → Z3 SAT → InvariantChecker(18) → │           │
│  │ ExploitAssembler (14 vulnerability types)        │           │
│  └────────────────────┬─────────────────────────────┘           │
│                       ▼                                         │
│  Layer 7: Heikal Math (Physics-Inspired)                        │
│  ┌──────────────────────────────────────────────────┐           │
│  │ Tunneling │ Wave │ Holographic │ Resonance       │           │
│  └────────────────────┬─────────────────────────────┘           │
│                       ▼                                         │
│  Dedup → RiskCore P(exploit) → PoC Gen → Report                │
└─────────────────────────────────────────────────────────────────┘
```

> For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## CLI Reference — مرجع سطر الأوامر

### `agl-security` — Standard CLI

| Command | Description | Example |
|---------|-------------|---------|
| `scan` | Standard file/directory scan | `agl-security scan contract.sol` |
| `quick` | Fast pattern-only scan (seconds) | `agl-security quick contract.sol` |
| `deep` | Full pipeline (Z3 + all layers) | `agl-security deep contract.sol` |
| `project` | Scan Foundry/Hardhat/Truffle project | `agl-security project ./my-project` |
| `info` | Project stats (no scan) | `agl-security info ./my-project` |
| `graph` | Dependency graph (JSON) | `agl-security graph ./my-project -o deps.json` |

**Common flags:**
- `-f json|markdown|text` — Output format (default: `text`)
- `-o report.md` — Save to file
- `-r, --recursive` — Scan subdirectories
- `-m quick|scan|deep` — Scan mode (project command)

**Exit codes:** `0` = clean, `1` = HIGH findings, `2` = CRITICAL findings

### `agl-audit` — Full Pipeline CLI

| Flag | Description |
|------|-------------|
| `--mode full\|deep\|quick` | Audit mode (default: `full`) |
| `--format json\|markdown\|text` | Output format (default: `json`) |
| `-o, --output PATH` | Output file path |
| `-b, --branch BRANCH` | Git branch for GitHub URLs |
| `--skip-heikal` | Skip Layer 7 Heikal Math |
| `--include-deps` | Scan node_modules/lib/ |
| `--include-tests` | Include test files |
| `--no-poc` | Skip PoC generation |
| `--run-poc` | Execute generated PoCs with Foundry |

---

## File Structure | هيكل الملفات

```
agl_security_tool/
├── __init__.py                  # Package exports (AGLSecurityAudit, ProjectScanner, ...)
├── __main__.py                  # CLI: agl-security (scan/quick/deep/project/info/graph)
├── audit_pipeline.py            # CLI: agl-audit (full 8-layer pipeline orchestrator)
├── core.py                      # AGLSecurityAudit — main analysis engine
├── project_scanner.py           # Foundry/Hardhat/Truffle project detection
├── solidity_flattener.py        # Import resolution + inheritance chain
├── z3_symbolic_engine.py        # Z3 SMT solver (8 check types)
├── exploit_reasoning.py         # Exploit proofs (14 vuln types, Z3 SAT)
├── risk_core.py                 # P(exploit) = σ(w·x + β) probability scoring
├── contract_intelligence.py     # Noisy-OR aggregation + MetaClassifier
├── poc_generator.py             # Foundry .t.sol PoC templates (9 types)
├── known_pattern_filter.py      # False positive suppression
├── onchain_context.py           # On-chain data integration (9 chains)
├── tool_backends.py             # Slither/Mythril/Semgrep wrappers
├── benchmark_runner.py          # SWC ground truth evaluation
├── weight_optimizer.py          # SGD risk weight training
├── vscode_bridge.py             # VS Code extension bridge
│
├── detectors/                   # Layer 5 — 22+ semantic detectors
├── state_extraction/            # Layer 1 — Financial state extraction
├── action_space/                # Layer 2 — Attack action enumeration
├── attack_engine/               # Layer 3 — Economic attack simulation
├── search_engine/               # Layer 4 — Guided economic search
├── heikal_math/                 # Layer 7 — Physics-inspired scoring
├── api/                         # REST API (FastAPI + JWT + WebSocket)
├── cli/                         # CLI utilities (manage, train)
│
├── tests/                       # Test suite (175+ tests)
├── training_contracts/          # Detector training data
├── test_contracts/              # Test Solidity contracts
├── bounty_contracts/            # Real-world audit targets
├── docs/                        # Documentation
│
├── Dockerfile                   # Multi-stage (CLI + API)
├── docker-compose.yml           # CLI + API services
├── pyproject.toml               # Package configuration
├── requirements.txt             # Dependencies
├── requirements-lock.txt        # Pinned versions
├── .env.example                 # Environment variables template
├── CHANGELOG.md                 # Version history
└── DEPLOYMENT.md                # Production deployment guide
```

---

## Dependencies | المتطلبات

### Required — مطلوبة

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | ≥ 2.28.0 | HTTP client |
| `z3-solver` | ≥ 4.12.0 | Z3 SMT symbolic execution |
| `numpy` | ≥ 1.24.0 | FFT for Holographic Memory |
| `pydantic` | ≥ 2.0.0 | Data model validation |
| `psutil` | ≥ 5.9.0 | System resource monitoring |

### Optional — اختيارية

| Package | Purpose |
|---------|---------|
| `slither-analyzer` | Static analysis (80+ detectors) |
| `mythril` | EVM symbolic execution |
| `semgrep` | Pattern-based scanning |
| `fastapi + uvicorn` | REST API server |

> See [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) for full dependency documentation, Docker setup, and troubleshooting.

---

## Testing | الاختبار

```bash
# Fast tests only (~20s)
python -m pytest tests/ -x --tb=short -q

# All tests including integration (~5min)
python -m pytest tests/ -m '' --timeout=300

# Specific test file
python -m pytest tests/test_detectors.py -v
```

---

## Documentation | التوثيق

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Full pipeline architecture & data flow |
| [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) | Dependencies, setup, Docker, troubleshooting |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment guide |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

---

## License

Part of the AGL Project — MIT License. See root [README.md](../README.md) for details.
