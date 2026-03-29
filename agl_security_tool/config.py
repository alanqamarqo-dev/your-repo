"""
AGL Security Tool — Centralized Configuration
نظام الإعدادات المركزي — يقرأ من .env ومتغيرات البيئة

Priority (highest first):
  1. Environment variables
  2. .env file in project root
  3. Defaults
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("AGL.config")


def _bool(val: str) -> bool:
    return val.strip().lower() in ("1", "true", "yes", "on")


def _int(val: str, default: int) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _load_dotenv(path: Optional[Path] = None) -> None:
    """Load .env file into os.environ (no external dependency)."""
    if path is None:
        path = Path(__file__).resolve().parent / ".env"
    if not path.is_file():
        return
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # Don't override existing env vars
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        _logger.debug("Failed to load .env: %s", e)


@dataclass(frozen=True)
class AGLConfig:
    """Immutable configuration for AGL Security Tool."""

    # ── Logging ──
    log_level: str = "INFO"
    log_file: str = ""
    log_format: str = "text"

    # ── Analysis Timeouts ──
    mythril_timeout: int = 120
    slither_timeout: int = 60
    semgrep_timeout: int = 30
    z3_timeout: int = 30

    # ── Skip Flags ──
    skip_llm: bool = True
    skip_heikal: bool = False
    skip_mythril: bool = False
    skip_slither: bool = False
    skip_semgrep: bool = False

    # ── PoC ──
    generate_poc: bool = True
    run_foundry: bool = False

    # ── API ──
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 2
    api_cors_origins: str = "*"
    rate_limit: str = "10/minute"

    # ── On-Chain ──
    rpc_url: str = ""
    etherscan_key: str = ""

    # ── MongoDB ──
    mongo_uri: str = ""
    mongo_db: str = "agl_security"

    def to_audit_kwargs(self) -> dict:
        """Convert config to kwargs for run_audit()."""
        return {
            "mythril_timeout": self.mythril_timeout,
            "skip_llm": self.skip_llm,
            "skip_heikal": self.skip_heikal,
            "generate_poc": self.generate_poc,
            "run_poc": self.run_foundry,
        }


def load_config(env_file: Optional[Path] = None) -> AGLConfig:
    """
    Load configuration from environment + .env file.

    Args:
        env_file: Path to .env file (default: project root/.env)

    Returns:
        Frozen AGLConfig instance
    """
    _load_dotenv(env_file)

    cfg = AGLConfig(
        log_level=os.getenv("AGL_LOG_LEVEL", "INFO").upper(),
        log_file=os.getenv("AGL_LOG_FILE", ""),
        log_format=os.getenv("AGL_LOG_FORMAT", "text"),
        mythril_timeout=_int(os.getenv("AGL_MYTHRIL_TIMEOUT", ""), 120),
        slither_timeout=_int(os.getenv("AGL_SLITHER_TIMEOUT", ""), 60),
        semgrep_timeout=_int(os.getenv("AGL_SEMGREP_TIMEOUT", ""), 30),
        z3_timeout=_int(os.getenv("AGL_Z3_TIMEOUT", ""), 30),
        skip_llm=_bool(os.getenv("AGL_SKIP_LLM", "true")),
        skip_heikal=_bool(os.getenv("AGL_SKIP_HEIKAL", "false")),
        skip_mythril=_bool(os.getenv("AGL_SKIP_MYTHRIL", "false")),
        skip_slither=_bool(os.getenv("AGL_SKIP_SLITHER", "false")),
        skip_semgrep=_bool(os.getenv("AGL_SKIP_SEMGREP", "false")),
        generate_poc=_bool(os.getenv("AGL_GENERATE_POC", "true")),
        run_foundry=_bool(os.getenv("AGL_RUN_FOUNDRY", "false")),
        api_host=os.getenv("AGL_API_HOST", "0.0.0.0"),
        api_port=_int(os.getenv("AGL_API_PORT", ""), 8000),
        api_workers=_int(os.getenv("AGL_API_WORKERS", ""), 2),
        api_cors_origins=os.getenv("AGL_API_CORS_ORIGINS", "*"),
        rate_limit=os.getenv("AGL_RATE_LIMIT", "10/minute"),
        rpc_url=os.getenv("AGL_RPC_URL", ""),
        etherscan_key=os.getenv("AGL_ETHERSCAN_KEY", ""),
        mongo_uri=os.getenv("AGL_MONGO_URI", ""),
        mongo_db=os.getenv("AGL_MONGO_DB", "agl_security"),
    )

    _logger.debug("Config loaded: log_level=%s, mythril_timeout=%d", cfg.log_level, cfg.mythril_timeout)
    return cfg


# Singleton — loaded once on first import
_config: Optional[AGLConfig] = None


def get_config() -> AGLConfig:
    """Get or create the global config singleton."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
