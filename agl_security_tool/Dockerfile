# AGL Security Tool — Production Container
# ==========================================
FROM python:3.12-slim AS base

LABEL maintainer="AGL Team"
LABEL description="AGL Security - Smart Contract Security Analyzer"
LABEL version="2.1.0"

# System deps for Z3 + solc
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install solc-select + solc 0.8.20
RUN pip install --no-cache-dir solc-select \
    && solc-select install 0.8.20 \
    && solc-select use 0.8.20

# Copy requirements first (Docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package
COPY . .
RUN pip install --no-cache-dir -e .

# Optional: install external tools
ARG INSTALL_SLITHER=false
ARG INSTALL_SEMGREP=false
RUN if [ "$INSTALL_SLITHER" = "true" ]; then pip install --no-cache-dir slither-analyzer; fi
RUN if [ "$INSTALL_SEMGREP" = "true" ]; then pip install --no-cache-dir semgrep; fi

# Create non-root user
RUN useradd -m -s /bin/bash agl
USER agl

# Default: CLI mode
ENTRYPOINT ["agl-security"]
CMD ["--help"]

# ==========================================
# API Server variant
# ==========================================
FROM base AS api

USER root
RUN pip install --no-cache-dir -e ".[api]"
USER agl

EXPOSE 8000

ENTRYPOINT ["uvicorn"]
CMD ["agl_security_tool.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
