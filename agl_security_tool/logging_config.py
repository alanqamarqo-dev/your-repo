"""
AGL Security — تهيئة نظام السجلات
Logging Configuration — Rotating File + JSON Format

Usage:
    from agl_security_tool.logging_config import setup_logging
    setup_logging()  # call once at startup
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    log_file: str = "",
    log_format: str = "text",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. Empty = stdout only.
        log_format: 'text' for human-readable, 'json' for JSON lines.
        max_bytes: Max size per log file before rotation.
        backup_count: Number of rotated backup files to keep.
    """
    # ── Try reading from config if available ──
    try:
        from agl_security_tool.config import settings
        level = level or settings.LOG_LEVEL
        log_file = log_file or settings.LOG_FILE
        log_format = log_format or settings.LOG_FORMAT
    except ImportError:
        pass

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    root.handlers.clear()

    # ── Formatter ──
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # ── Console handler (always) ──
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    root.addHandler(console)

    # ── File handler (optional) ──
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    # ── Quiet noisy third-party loggers ──
    for noisy in ("urllib3", "httpcore", "httpx", "asyncio", "watchfiles"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    root.debug("Logging initialized: level=%s, file=%s, format=%s", level, log_file or "(stdout)", log_format)
