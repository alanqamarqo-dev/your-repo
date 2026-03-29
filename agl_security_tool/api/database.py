"""
AGL Security — Database Layer (SQLite + SQLAlchemy)
طبقة قاعدة البيانات — SQLite

Stores scan history, users, API keys, and reports.
"""

import os
import datetime
import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    JSON,
    Enum as SAEnum,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

# ── Database path ──────────────────────────────────────────
_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = os.environ.get("AGL_DB_PATH", str(_DB_DIR / "agl_security.db"))

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Helper ─────────────────────────────────────────────────
def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


# ═══════════════════════════════════════════════════════════
#  Models
# ═══════════════════════════════════════════════════════════


class User(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    hashed_pw = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_now)
    last_login = Column(DateTime, nullable=True)

    # relationships
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    scans = relationship("Scan", back_populates="user", cascade="all, delete-orphan")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(32), primary_key=True, default=_uuid)
    key = Column(String(64), unique=True, nullable=False, index=True)
    label = Column(String(100), default="default")
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)
    last_used = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_keys")


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String(32), primary_key=True, default=_uuid)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False)
    target_name = Column(String(500), nullable=False)  # filename or URL
    target_type = Column(String(20), default="file")  # file | url | project
    scan_mode = Column(String(20), default="deep")  # quick | scan | deep
    status = Column(
        String(20), default="pending"
    )  # pending | running | completed | failed
    progress = Column(Integer, default=0)  # 0-100
    current_layer = Column(String(100), default="")  # current layer being processed

    # Results summary
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    security_score = Column(Float, default=0.0)  # 0-100

    # Heikal Math
    heikal_xi = Column(Float, nullable=True)
    heikal_wave = Column(Float, nullable=True)
    heikal_tunnel = Column(Float, nullable=True)
    heikal_holo = Column(Float, nullable=True)
    heikal_resonance = Column(Float, nullable=True)

    # Full result (JSON blob)
    result_json = Column(JSON, nullable=True)

    # Attack simulation summary
    total_attacks = Column(Integer, default=0)
    profitable_attacks = Column(Integer, default=0)
    max_profit_usd = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=_now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_sec = Column(Float, default=0.0)

    # Error
    error_message = Column(Text, nullable=True)

    user = relationship("User", back_populates="scans")


# ═══════════════════════════════════════════════════════════
#  Init & Helpers
# ═══════════════════════════════════════════════════════════


def init_db():
    """Create all tables (idempotent)."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """FastAPI dependency — yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Direct session for background tasks."""
    return SessionLocal()
