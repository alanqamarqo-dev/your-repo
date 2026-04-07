"""
AGL Security — نظام الإعدادات المركزي
Centralized Configuration (reads from environment / .env)

Usage:
    from agl_security_tool.config import settings
    print(settings.LOG_LEVEL)
    print(settings.Z3_TIMEOUT)
"""

import os
from pathlib import Path
from dataclasses import dataclass, field

# ── Load .env file if present ──
_ENV_FILE = Path(__file__).parent.parent / ".env"
if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            os.environ.setdefault(key, value)


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int = 0) -> int:
    try:
        return int(os.environ.get(key, str(default)))
    except ValueError:
        return default


def _env_bool(key: str, default: bool = False) -> bool:
    val = os.environ.get(key, str(default)).lower()
    return val in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    """Immutable application settings — loaded once at import time."""

    # ── General ──
    APP_NAME: str = "AGL Security Tool"
    VERSION: str = "2.1.0"
    DEBUG: bool = field(default_factory=lambda: _env_bool("AGL_DEBUG", False))

    # ── Logging ──
    LOG_LEVEL: str = field(default_factory=lambda: _env("AGL_LOG_LEVEL", "INFO"))
    LOG_FILE: str = field(default_factory=lambda: _env("AGL_LOG_FILE", ""))
    LOG_FORMAT: str = field(default_factory=lambda: _env("AGL_LOG_FORMAT", "text"))  # text | json

    # ── Analysis Timeouts (seconds) ──
    Z3_TIMEOUT: int = field(default_factory=lambda: _env_int("AGL_Z3_TIMEOUT", 30))
    MYTHRIL_TIMEOUT: int = field(default_factory=lambda: _env_int("AGL_MYTHRIL_TIMEOUT", 120))
    SLITHER_TIMEOUT: int = field(default_factory=lambda: _env_int("AGL_SLITHER_TIMEOUT", 60))
    SEMGREP_TIMEOUT: int = field(default_factory=lambda: _env_int("AGL_SEMGREP_TIMEOUT", 60))
    PIPELINE_TIMEOUT: int = field(default_factory=lambda: _env_int("AGL_PIPELINE_TIMEOUT", 300))

    # ── API Server ──
    API_HOST: str = field(default_factory=lambda: _env("AGL_API_HOST", "0.0.0.0"))
    API_PORT: int = field(default_factory=lambda: _env_int("AGL_API_PORT", 8000))
    API_WORKERS: int = field(default_factory=lambda: _env_int("AGL_WORKERS", 2))
    API_RATE_LIMIT: str = field(default_factory=lambda: _env("AGL_RATE_LIMIT", "30/minute"))
    CORS_ORIGINS: str = field(default_factory=lambda: _env("AGL_CORS_ORIGINS", ""))

    # ── Auth ──
    SECRET_KEY: str = field(default_factory=lambda: _env("AGL_SECRET_KEY", ""))
    JWT_ALGORITHM: str = field(default_factory=lambda: _env("AGL_JWT_ALGORITHM", "HS256"))
    JWT_EXPIRY_HOURS: int = field(default_factory=lambda: _env_int("AGL_JWT_EXPIRY_HOURS", 24))

    # ── Database ──
    DATABASE_URL: str = field(default_factory=lambda: _env("AGL_DATABASE_URL", "sqlite:///agl_security.db"))
    MONGO_URI: str = field(default_factory=lambda: _env("AGL_MONGO_URI", ""))

    # ── External Tools ──
    SOLC_PATH: str = field(default_factory=lambda: _env("AGL_SOLC_PATH", ""))
    RPC_URL: str = field(default_factory=lambda: _env("AGL_RPC_URL", ""))
    ETHERSCAN_API_KEY: str = field(default_factory=lambda: _env("AGL_ETHERSCAN_API_KEY", ""))

    # ── Paths ──
    ARTIFACTS_DIR: str = field(
        default_factory=lambda: _env("AGL_ARTIFACTS_DIR", str(Path(__file__).parent / "artifacts"))
    )
    REPORTS_DIR: str = field(
        default_factory=lambda: _env("AGL_REPORTS_DIR", str(Path(__file__).parent / "reports"))
    )


# ── Singleton ──
settings = Settings()
