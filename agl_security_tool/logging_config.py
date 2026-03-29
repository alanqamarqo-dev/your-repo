"""
AGL Security Tool — Logging Setup
إعداد السجلات — ملفات + دوران + JSON

Usage:
    from agl_security_tool.logging_config import setup_logging
    setup_logging()  # Uses config from get_config()
"""

from __future__ import annotations

import logging
import logging.handlers
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


_TEXT_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: str = "INFO",
    log_file: str = "",
    log_format: str = "text",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """
    Configure root logger with console + optional rotating file handler.

    Args:
        level:        Log level (DEBUG, INFO, WARNING, ERROR)
        log_file:     Path for log file. Empty = console only.
        log_format:   'text' or 'json'
        max_bytes:    Max size per log file before rotation
        backup_count: Number of rotated files to keep
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers to avoid duplicates
    root.handlers.clear()

    # Console handler
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG)
    if log_format == "json":
        console.setFormatter(JSONFormatter())
    else:
        console.setFormatter(logging.Formatter(_TEXT_FORMAT, _DATE_FORMAT))
    root.addHandler(console)

    # File handler (rotating)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        if log_format == "json":
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(_TEXT_FORMAT, _DATE_FORMAT))
        root.addHandler(file_handler)

        logging.getLogger("AGL.config").info(
            "File logging enabled: %s (max=%dMB, keep=%d)",
            log_path, max_bytes // (1024 * 1024), backup_count,
        )

    # Quiet noisy third-party loggers
    for name in ("urllib3", "asyncio", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)


def setup_from_config() -> None:
    """Setup logging using the global AGLConfig."""
    from agl_security_tool.config import get_config
    cfg = get_config()
    setup_logging(
        level=cfg.log_level,
        log_file=cfg.log_file,
        log_format=cfg.log_format,
    )
