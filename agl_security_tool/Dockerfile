# AGL Security Tool - Multi-stage Dockerfile
# ============================================
# Build targets:
#   docker build -t agl-security .                                # CLI (default)
#   docker build --target api -t agl-security-api .               # API server
#   docker build --target audit -t agl-audit .                    # Full pipeline
#
# With external tools:
#   docker build --build-arg INSTALL_SLITHER=true --build-arg INSTALL_SEMGREP=true -t agl-security .

# ── Stage 1: Base (CLI) ──
FROM python:3.12-slim AS base

LABEL maintainer="AGL Team"
LABEL description="AGL Smart Contract Security Analyzer v2.1.0"
LABEL version="2.1.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

ARG INSTALL_SLITHER="false"
ARG INSTALL_SEMGREP="false"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git && \
    rm -rf /var/lib/apt/lists/*

# Python deps — install first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optional: external security tools
RUN if [ "$INSTALL_SLITHER" = "true" ]; then pip install --no-cache-dir slither-analyzer; fi
RUN if [ "$INSTALL_SEMGREP" = "true" ]; then pip install --no-cache-dir semgrep; fi

# Copy source (the package lives at repo_root/agl_security_tool/)
# Context is the agl_security_tool/ directory itself
COPY pyproject.toml setup.cfg* ./agl_security_tool/
COPY requirements.txt requirements-lock.txt ./agl_security_tool/
COPY __init__.py __main__.py core.py audit_pipeline.py ./agl_security_tool/agl_security_tool/
COPY detectors/ ./agl_security_tool/agl_security_tool/detectors/
COPY state_extraction/ ./agl_security_tool/agl_security_tool/state_extraction/
COPY action_space/ ./agl_security_tool/agl_security_tool/action_space/
COPY attack_engine/ ./agl_security_tool/agl_security_tool/attack_engine/
COPY search_engine/ ./agl_security_tool/agl_security_tool/search_engine/
COPY heikal_math/ ./agl_security_tool/agl_security_tool/heikal_math/
COPY *.py ./agl_security_tool/agl_security_tool/

# Install package
RUN pip install --no-cache-dir -e ./agl_security_tool

# Default: CLI mode
ENTRYPOINT ["agl-security"]
CMD ["--help"]

# ── Stage 2: Full Pipeline ──
FROM base AS audit

ENTRYPOINT ["agl-audit"]
CMD ["--help"]

# ── Stage 3: API Server ──
FROM base AS api

# Install API extras
COPY api/ ./agl_security_tool/agl_security_tool/api/
RUN pip install --no-cache-dir -e "./agl_security_tool[api]"

EXPOSE 8000

# Non-root user for security
RUN useradd -m -r agluser && chown -R agluser:agluser /app
USER agluser

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "agl_security_tool.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
