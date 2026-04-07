# Deployment Guide — AGL Security Tool

## Quick Start

```bash
# 1. Clone & install
git clone https://github.com/your-org/your-repo.git
cd your-repo
pip install -e ".[api,dev]"

# 2. Configure
cp .env.example .env
# Edit .env — set AGL_SECRET_KEY at minimum

# 3. Run CLI scan
agl-security scan contract.sol
agl-security scan contracts/ --recursive -f json -o report.json

# 4. Run API server
uvicorn agl_security_tool.api.server:app --port 8000
```

## Docker Deployment

### CLI Mode (one-shot scan)
```bash
docker compose up agl-cli
```

### API Server
```bash
# Foreground
docker compose up agl-api

# Background (daemon)
docker compose up agl-api -d

# Check health
curl http://localhost:8000/health
```

### Build with External Tools
```bash
docker compose build --build-arg INSTALL_SLITHER=true --build-arg INSTALL_SEMGREP=true
```

## Production Deployment

### Environment Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGL_SECRET_KEY` | **Yes** | — | JWT signing key (≥32 hex chars) |
| `AGL_LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `AGL_LOG_FILE` | No | — | Path for rotating log file |
| `AGL_LOG_FORMAT` | No | `text` | `text` or `json` |
| `AGL_API_PORT` | No | `8000` | API listen port |
| `AGL_WORKERS` | No | `2` | Uvicorn workers |
| `AGL_RATE_LIMIT` | No | `30/minute` | API rate limit |
| `AGL_CORS_ORIGINS` | No | — | Comma-separated allowed origins |
| `AGL_DATABASE_URL` | No | `sqlite:///agl_security.db` | DB connection string |
| `AGL_Z3_TIMEOUT` | No | `30` | Z3 solver timeout (seconds) |
| `AGL_PIPELINE_TIMEOUT` | No | `300` | Full pipeline timeout (seconds) |

### Generate Secret Key
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Reverse Proxy (nginx)
```nginx
server {
    listen 443 ssl;
    server_name agl.yourdomain.com;

    ssl_certificate /etc/ssl/certs/agl.pem;
    ssl_certificate_key /etc/ssl/private/agl.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## CLI Reference

```bash
# Standard scan
agl-security scan contract.sol

# Deep scan (all 8 layers)
agl-security deep contract.sol

# Quick scan (detectors only)
agl-security quick contract.sol

# Full project scan (Foundry/Hardhat)
agl-security project /path/to/project -m deep -f json -o report.json

# Full audit pipeline
agl-audit --file contract.sol --mode full --output report.json
```

## Testing

```bash
# Install dev deps
pip install -e ".[dev]"

# Core tests (fast, ~3s)
python -m pytest tests/test_detectors.py tests/test_solidity_parser.py tests/test_risk_core.py tests/test_contract_intelligence.py -v

# Pipeline integration tests
python -m pytest tests/test_pipeline_integration.py tests/test_pipeline_fixes.py tests/test_pipeline_accuracy.py -v

# All tests
python -m pytest tests/ -v
```

## Pre-Deploy Checklist

- [ ] `AGL_SECRET_KEY` set to unique random value
- [ ] `AGL_CORS_ORIGINS` restricted to your frontend domain(s)
- [ ] `AGL_LOG_FILE` configured for production logging
- [ ] `AGL_LOG_FORMAT=json` for structured log aggregation
- [ ] Database URL pointing to production DB (not SQLite)
- [ ] Reverse proxy with TLS configured
- [ ] Rate limiting appropriate for your users
- [ ] Docker image built with `--no-cache` for fresh install
- [ ] Health check endpoint responding: `curl http://localhost:8000/health`
- [ ] Core tests passing: `python -m pytest tests/ -v`
