# 🔧 Environment & Dependencies Guide — دليل البيئة والاعتمادات

> **الإصدار:** 2.1.0  
> **آخر تحديث:** أبريل 2026

---

## 📑 فهرس المحتويات

1. [Python Requirements](#1-python-requirements)
2. [Core Dependencies](#2-core-dependencies)
3. [Optional Dependencies](#3-optional-dependencies)
4. [External Tools](#4-external-tools)
5. [Environment Variables](#5-environment-variables)
6. [Installation Methods](#6-installation-methods)
7. [Docker Environment](#7-docker-environment)
8. [Compatibility Matrix](#8-compatibility-matrix)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Python Requirements

| Requirement | Value |
|------------|-------|
| **Minimum Python** | 3.10 |
| **Recommended** | 3.12 |
| **Tested on** | 3.10, 3.11, 3.12, 3.13 |
| **Platform** | Windows, Linux, macOS |

---

## 2. Core Dependencies — الاعتمادات الأساسية

These are **required** for the tool to function:

| Package | Min Version | Pinned (Lock) | Purpose / الغرض |
|---------|-------------|---------------|-----------------|
| `requests` | ≥ 2.28.0 | 2.31.0 | HTTP client for external APIs, GitHub cloning |
| `z3-solver` | ≥ 4.12.0 | 4.16.0 | Z3 SMT symbolic execution engine (Layer 0.5 + Layer 6) |
| `numpy` | ≥ 1.24.0 | 2.4.3 | FFT in Holographic Pattern Memory (Layer 7), numerical ops |
| `pydantic` | ≥ 2.0.0 | 2.12.5 | Data validation models (state_extraction, attack_engine) |
| `psutil` | ≥ 5.9.0 | 7.2.2 | System resource monitoring, process management |

### Install Core Only
```bash
pip install requests z3-solver numpy pydantic psutil
# or
pip install -e .
```

---

## 3. Optional Dependencies — اعتمادات اختيارية

### 3.1 API Server (`pip install -e ".[api]"`)

| Package | Min Version | Pinned | Purpose |
|---------|-------------|--------|---------|
| `fastapi` | ≥ 0.100.0 | 0.135.2 | Web framework for REST API + WebSocket |
| `uvicorn` | ≥ 0.22.0 | 0.42.0 | ASGI server (production + dev) |
| `python-jose[cryptography]` | ≥ 3.3.0 | 3.3.0 | JWT token generation & validation |
| `bcrypt` | ≥ 4.0.0 | 4.2.1 | Password hashing (direct bcrypt, NOT passlib) |
| `sqlalchemy` | ≥ 2.0.0 | 2.0.48 | Database ORM (SQLite default, PostgreSQL optional) |
| `slowapi` | ≥ 0.1.0 | 0.1.9 | Rate limiting middleware |
| `python-multipart` | ≥ 0.0.5 | 0.0.20 | File upload parsing |

> ⚠️ **Important:** We use `bcrypt` directly, NOT `passlib`. The `passlib` library has compatibility issues with `bcrypt >= 4.1`.

### 3.2 MongoDB (`pip install -e ".[mongo]"`)

| Package | Min Version | Purpose |
|---------|-------------|---------|
| `pymongo` | ≥ 4.0.0 | MongoDB driver for persistent audit storage |

### 3.3 Development (`pip install -e ".[dev]"`)

| Package | Min Version | Purpose |
|---------|-------------|---------|
| `pytest` | ≥ 7 | Test framework |

---

## 4. External Tools — أدوات خارجية

These are **optional** and enhance detection. The tool works **100% standalone** without them.

| Tool | Install Command | Purpose | Layer |
|------|----------------|---------|-------|
| `solc` | `pip install solc-select` | Solidity compiler (required by Slither) | — |
| `slither-analyzer` | `pip install slither-analyzer` | Static analysis (80+ detectors) | L1 |
| `mythril` | `pip install mythril` | EVM symbolic execution | L1 |
| `semgrep` | `pip install semgrep` | Pattern-based rule scanning | L1 |
| `forge` (Foundry) | `curl -L https://foundry.paradigm.xyz \| bash` | PoC test execution | L8.7 |

### Solc Setup
```bash
pip install solc-select
solc-select install 0.8.19
solc-select use 0.8.19
```

---

## 5. Environment Variables — متغيرات البيئة

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### General
| Variable | Default | Description |
|----------|---------|-------------|
| `AGL_DEBUG` | `false` | Enable debug mode |
| `AGL_LOG_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `AGL_LOG_FILE` | *(empty)* | File path for log output, empty = stdout only |
| `AGL_LOG_FORMAT` | `text` | Log format: `text` or `json` |

### Analysis Timeouts (seconds)
| Variable | Default | Description |
|----------|---------|-------------|
| `AGL_Z3_TIMEOUT` | `30` | Z3 solver max time per check |
| `AGL_MYTHRIL_TIMEOUT` | `120` | Mythril EVM analysis timeout |
| `AGL_SLITHER_TIMEOUT` | `60` | Slither static analysis timeout |
| `AGL_SEMGREP_TIMEOUT` | `60` | Semgrep scanning timeout |
| `AGL_PIPELINE_TIMEOUT` | `300` | Full pipeline max time |

### API Server
| Variable | Default | Description |
|----------|---------|-------------|
| `AGL_API_HOST` | `0.0.0.0` | Listen address |
| `AGL_API_PORT` | `8000` | Listen port |
| `AGL_WORKERS` | `2` | Uvicorn worker count |
| `AGL_RATE_LIMIT` | `30/minute` | API rate limit |
| `AGL_CORS_ORIGINS` | *(empty)* | Comma-separated CORS origins |

### Auth (REQUIRED for production API)
| Variable | Default | Description |
|----------|---------|-------------|
| `AGL_SECRET_KEY` | — | **REQUIRED.** JWT signing key |
| `AGL_JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `AGL_JWT_EXPIRY_HOURS` | `24` | Token expiry time |

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Database
| Variable | Default | Description |
|----------|---------|-------------|
| `AGL_DATABASE_URL` | `sqlite:///agl_security.db` | SQLAlchemy connection string |
| `AGL_MONGO_URI` | *(empty)* | MongoDB URI (optional) |

### External Tools
| Variable | Default | Description |
|----------|---------|-------------|
| `AGL_SOLC_PATH` | *(auto)* | Path to solc binary |
| `AGL_RPC_URL` | *(empty)* | Ethereum JSON-RPC URL for on-chain context |
| `AGL_ETHERSCAN_API_KEY` | *(empty)* | Etherscan API key for source verification |

### Paths
| Variable | Default | Description |
|----------|---------|-------------|
| `AGL_ARTIFACTS_DIR` | `./artifacts` | Directory for model artifacts |
| `AGL_REPORTS_DIR` | `./reports` | Directory for audit reports |

---

## 6. Installation Methods — طرق التثبيت

### 6.1 Standard Install (Recommended)
```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo/agl_security_tool
pip install -e .
```

### 6.2 Full Install (CLI + API + Dev)
```bash
pip install -e ".[api,dev]"
```

### 6.3 From requirements.txt
```bash
pip install -r requirements.txt        # Core + API deps
pip install -r requirements-lock.txt   # Exact pinned versions
```

### 6.4 Docker (see section 7)
```bash
docker compose up agl-cli   # CLI mode
docker compose up agl-api   # API server
```

### Verify Installation
```bash
# CLI works
agl-security --help
agl-audit --help

# Python import works
python -c "from agl_security_tool import AGLSecurityAudit; print('OK')"

# Run tests
python -m pytest tests/ -x --tb=short -q

# Full pipeline test (takes ~4 min)
python -m pytest tests/ -m slow --timeout=300
```

---

## 7. Docker Environment — بيئة Docker

### 7.1 Docker Images

Two build targets:

| Target | Image | Entrypoint | Use Case |
|--------|-------|------------|----------|
| `base` | `agl-security` | `agl-security` CLI | One-shot scans |
| `api` | `agl-security-api` | `uvicorn` | REST API server |

### 7.2 Build Commands
```bash
# CLI image
docker build -t agl-security .

# API image
docker build --target api -t agl-security-api .

# With external tools
docker build --build-arg INSTALL_SLITHER=true --build-arg INSTALL_SEMGREP=true -t agl-security .
```

### 7.3 Docker Compose
```bash
# CLI scan
docker compose up agl-cli

# API server (foreground)
docker compose up agl-api

# API server (background)
docker compose up agl-api -d

# Check health
curl http://localhost:8000/health
```

### 7.4 Docker Volumes

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./contracts` | `/contracts` (ro) | Input contracts to scan |
| `./reports` | `/reports` | Output audit reports |
| `./logs` | `/app/logs` | Application logs |

---

## 8. Compatibility Matrix — مصفوفة التوافق

| Component | Python 3.10 | Python 3.11 | Python 3.12 | Python 3.13 |
|-----------|-------------|-------------|-------------|-------------|
| Core Engine | ✅ | ✅ | ✅ | ✅ |
| Z3 Symbolic | ✅ | ✅ | ✅ | ✅ |
| 22 Detectors | ✅ | ✅ | ✅ | ✅ |
| Exploit Reasoning | ✅ | ✅ | ✅ | ✅ |
| Heikal Math | ✅ | ✅ | ✅ | ✅ |
| State Extraction | ✅ | ✅ | ✅ | ✅ |
| FastAPI Server | ✅ | ✅ | ✅ | ✅ |
| Slither | ✅ | ✅ | ✅ | ⚠️ |
| Mythril | ✅ | ✅ | ✅ | ❌ |

> ⚠️ Slither on Python 3.13 may require latest version. Mythril currently has limited 3.13 support.

### OS Compatibility

| Feature | Windows | Linux | macOS |
|---------|---------|-------|-------|
| Core Analysis | ✅ | ✅ | ✅ |
| Docker (CLI) | ✅ | ✅ | ✅ |
| Docker (API) | ✅ | ✅ | ✅ |
| Foundry PoC | ⚠️ WSL | ✅ | ✅ |
| Slither | ✅ | ✅ | ✅ |

---

## 9. Troubleshooting — استكشاف الأخطاء

### `z3-solver` installation fails
```bash
# On Windows, ensure Visual C++ Build Tools are installed
pip install z3-solver --no-build-isolation

# On Linux
sudo apt install libz3-dev
pip install z3-solver
```

### `bcrypt` errors
```bash
# We use bcrypt directly, NOT passlib
# If you see "passlib" errors, run:
pip uninstall passlib
pip install bcrypt>=4.0.0
```

### Import errors: `ModuleNotFoundError: agl_security_tool`
```bash
# Ensure the package is installed in editable mode
cd agl_security_tool/
pip install -e .
```

### Slither `solc` not found
```bash
pip install solc-select
solc-select install 0.8.19
solc-select use 0.8.19
```

### Tests hanging
```bash
# Run only fast tests (excludes heavy integration tests)
python -m pytest tests/ -m 'not slow' --tb=short -q

# Run with timeout safety
python -m pytest tests/ --timeout=60
```

### Docker build fails
```bash
# Clean Docker cache
docker builder prune

# Build without external tools (faster)
docker build --build-arg INSTALL_SLITHER=false --build-arg INSTALL_SEMGREP=false -t agl-security .
```
