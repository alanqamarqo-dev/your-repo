# 🛡️ AGL Security — Smart Contract Security Auditor

أداة تحليل أمان العقود الذكية متعددة الطبقات مع إثبات رياضي Z3.

## 🏗️ Architecture

```
agl_security_tool/          ← Python package (واجهة موحدة)
├── __init__.py             ← Entry: from agl_security_tool import AGLSecurityAudit
├── __main__.py             ← CLI: python -m agl_security_tool scan contract.sol
└── core.py                 ← AGLSecurityAudit class

AGL_NextGen/src/agl/engines/   ← Analysis engines (محركات التحليل)
├── smart_contract_analyzer.py ← Layer 1: Solidity Lexer + CFG + Taint + 8 pattern detectors
├── agl_security.py            ← Layer 2: Slither/Mythril/Semgrep wrapper + filter/dedup
├── offensive_security.py      ← Layer 3: Full pipeline (Heuristic + Z3 + EVM Sim + LLM)
├── formal_verifier.py         ← Z3 SMT Solver for mathematical proofs
├── solidity_context_aggregator.py ← Cross-contract import resolver
├── holographic_llm.py         ← LLM wrapper (Ollama/OpenAI)
├── strict_logic/              ← AND/OR/NOT/XOR/NAND logic gates
│   ├── logic_gates.py
│   └── observable.py
└── __init__.py

manage.py                   ← Management script (سكربت الإدارة)
vulnerable.sol              ← Test contract with 4 known vulnerabilities
```

## ⚡ Quick Start

```bash
# 1. Install
pip install -r requirements_security.txt

# 2. Check environment
python manage.py check

# 3. Scan a contract
python manage.py scan path/to/contract.sol

# 4. Deep scan (Z3 + EVM simulation + LLM)
python manage.py deep path/to/contract.sol

# 5. Generate report
python manage.py report path/to/contract.sol
```

## 🐍 Python API

```python
from agl_security_tool import AGLSecurityAudit

audit = AGLSecurityAudit()

# Quick scan — patterns only (fast)
result = audit.quick_scan("contract.sol")

# Standard scan — Layer 1 + Layer 2
result = audit.scan("contract.sol")

# Deep scan — Full pipeline with Z3 proofs
result = audit.deep_scan("contract.sol")

# Scan directory
result = audit.scan("contracts/", recursive=True)

# Generate report
print(audit.generate_report(result, format="markdown"))
```

## 🖥️ CLI

```bash
# Standard scan
python -m agl_security_tool scan contract.sol

# Quick scan (patterns only)
python -m agl_security_tool quick contract.sol

# Deep scan
python -m agl_security_tool deep contract.sol

# Output formats
python -m agl_security_tool scan contract.sol -f json -o result.json
python -m agl_security_tool scan contract.sol -f markdown -o report.md
```

## 🔬 Detection Capabilities

### Layer 1: Pattern Scanner (`smart_contract_analyzer.py`)
| Pattern | Severity | ID |
|---------|----------|----|
| Reentrancy (call before state update) | CRITICAL | REENTRANCY-001 |
| tx.origin authentication | HIGH | TXORIGIN-001 |
| Unchecked low-level call | MEDIUM | UNCHECKED-001 |
| Arbitrary ETH send | HIGH | ARBSEND-001 |
| Block timestamp dependency | LOW | TIMESTAMP-001 |
| Dangerous delegatecall | CRITICAL | DELEGATECALL-001 |
| Missing zero address check | LOW | ZEROCHECK-001 |
| Integer overflow (< 0.8.0) | HIGH | OVERFLOW-001 |

### Layer 2: Security Suite (`agl_security.py`)
- **Slither** integration (if installed)
- **Mythril** integration (if installed)
- **Semgrep** integration (if installed)
- Automatic deduplication & severity filtering

### Layer 3: Offensive Engine (`offensive_security.py`)
- 🔬 **Z3 Formal Verification** — Mathematical proofs (SAT/UNSAT)
- 🔰 **Strict Logic Gates** — AND/OR/NOT severity classification
- 🧿 **Quantum Neural Core** — State-space vulnerability discovery
- ♟️ **Meta-Reasoner** — Strategic analysis via LLM
- 🧠 **Holographic Memory** — Cache + LLM wrapper
- ⚛️ **Resonance Optimizer** — Exploit matching
- 🔧 **EVM Simulation** — Dynamic money-flow analysis with Z3 proofs

## 📊 manage.py Commands

| Command | Description |
|---------|-------------|
| `install` | تثبيت المتطلبات — Install dependencies |
| `check` | فحص صحة البيئة — Health check |
| `status` | حالة المحركات — Engine status |
| `test` | تشغيل الاختبارات — Run tests |
| `scan <path>` | فحص قياسي — Standard scan |
| `quick <path>` | فحص سريع — Pattern-only scan |
| `deep <path>` | فحص عميق — Full pipeline |
| `report <path>` | فحص + تقرير — Scan + Markdown report |
| `benchmark` | اختبار أداء — Performance benchmark |
| `clean` | تنظيف الكاش — Clean cache |

## 🔧 Optional: Ollama LLM

For AI-enhanced analysis, install [Ollama](https://ollama.ai) and pull a model:

```bash
ollama pull qwen2.5:3b-instruct
```

The tool works without LLM — it's just an extra layer.

## 📄 License

Internal tool — AGL Team.
