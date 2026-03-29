# Deployment Guide

## Quick Start

### Option 1: pip install (local)

```bash
# Clone
git clone https://github.com/your-org/your-repo.git
cd your-repo

# Install
pip install -e .

# Run
agl-security scan contract.sol
agl-security deep contract.sol -f json -o report.json
agl-security project ./my-project -m deep
```

### Option 2: Docker (recommended for production)

```bash
# Build
docker compose build

# Scan a contract
docker compose run agl-cli scan /contracts/MyToken.sol

# Start API server
docker compose up agl-api -d

# View logs
docker compose logs -f agl-api
```

### Option 3: Docker with external tools

```bash
docker compose build --build-arg INSTALL_SLITHER=true --build-arg INSTALL_SEMGREP=true
```

---

## Configuration

Copy `.env.example` to `.env` and modify:

```bash
cp .env.example .env
```

Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `AGL_LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `AGL_LOG_FILE` | _(empty)_ | Path for log file. Empty = console only |
| `AGL_MYTHRIL_TIMEOUT` | `120` | Mythril analysis timeout (seconds) |
| `AGL_SKIP_LLM` | `true` | Skip LLM analysis |
| `AGL_GENERATE_POC` | `true` | Generate Foundry PoC tests |
| `AGL_RUN_FOUNDRY` | `false` | Auto-run Foundry on generated PoCs |
| `AGL_API_PORT` | `8000` | API server port |
| `AGL_RATE_LIMIT` | `10/minute` | API rate limit |
| `AGL_RPC_URL` | _(empty)_ | Ethereum RPC for on-chain context |

---

## CLI Commands

```bash
# Basic scan
agl-security scan contract.sol

# Quick scan (pattern only, no Z3)
agl-security quick contract.sol

# Deep scan (full 8-layer pipeline)
agl-security deep contract.sol

# Project scan (Foundry/Hardhat/Truffle)
agl-security project ./my-project -m deep

# Output formats
agl-security scan contract.sol -f json -o report.json
agl-security scan contract.sol -f markdown -o report.md

# Project info (no scan)
agl-security info ./my-project
```

---

## API Server

```bash
# Install API dependencies
pip install -e ".[api]"

# Start server
uvicorn agl_security_tool.api.main:app --host 0.0.0.0 --port 8000

# Or via Docker
docker compose up agl-api -d
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/scan` | Upload & scan a .sol file |
| `POST` | `/api/project` | Scan a project directory |
| `GET` | `/api/reports/{id}` | Get scan report by ID |
| `GET` | `/health` | Health check |

---

## External Tools (Optional)

AGL works standalone, but external tools enhance coverage:

| Tool | Install | Purpose |
|------|---------|---------|
| **Slither** | `pip install slither-analyzer` | Static analysis (33+ detectors) |
| **Semgrep** | `pip install semgrep` | Pattern matching (custom rules) |
| **Mythril** | `pip install mythril` | Symbolic execution (Python ≤3.12) |
| **Foundry** | `curl -L https://foundry.paradigm.xyz \| bash` | PoC test execution |
| **solc** | `pip install solc-select && solc-select install 0.8.20` | Solidity compiler |

---

## Production Checklist

- [ ] Copy `.env.example` to `.env` and configure
- [ ] Set `AGL_LOG_FILE` for persistent logging
- [ ] Set `AGL_LOG_LEVEL=WARNING` for production
- [ ] Install external tools (Slither, Semgrep) for full coverage
- [ ] Set up TLS/reverse proxy (nginx) in front of API
- [ ] Configure rate limiting via `AGL_RATE_LIMIT`
- [ ] Set up log rotation (built-in: 10MB × 5 files)
- [ ] Monitor `/health` endpoint
- [ ] Back up `artifacts/risk_weights.json` (trained model)

---

## Architecture

```
Layer 0: Shared Parsing (AST + regex fallback)
Layer 1: State Extraction Engine
Layer 2: Action Space Analysis
Layer 3: Attack Simulation Engine
Layer 4: Intelligent Search Engine
Layer 5: Deep Scan (Slither + Mythril + Semgrep)
Layer 6: Z3 Symbolic Engine + Exploit Reasoning
Layer 7: Heikal Math + Contract Intelligence
Layer 8: Cross-Layer Dedup + PoC Generation
```

39 semantic detectors, Z3 formal verification, trained risk weights,
dynamic PoC generation with Foundry execution.
