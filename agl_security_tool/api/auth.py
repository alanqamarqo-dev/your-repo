"""
AGL Security — Authentication (JWT + API Key)
نظام المصادقة — JWT + مفتاح API

Handles:
  - Password hashing (bcrypt via passlib)
  - JWT token creation / verification
  - API key generation / validation
"""

import os
import sys
import secrets
import datetime
from pathlib import Path
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Security, Query, WebSocket
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
    APIKeyHeader,
)
from sqlalchemy.orm import Session

from .database import get_db, User, APIKey

# ── Configuration ──────────────────────────────────────────
# Production: AGL_SECRET_KEY MUST be set in environment.
# Development: auto-generates but persists to data/.secret_key file so
#              tokens survive server restarts.
_AGL_ENV = os.environ.get("AGL_ENV", "development")  # "production" | "development"


def _resolve_secret_key() -> str:
    """Resolve SECRET_KEY with production safety."""
    env_key = os.environ.get("AGL_SECRET_KEY")
    if env_key:
        return env_key

    # In production, refuse to start without an explicit key
    if _AGL_ENV == "production":
        print(
            "\n🔴 FATAL: AGL_SECRET_KEY is not set!\n"
            "   In production mode, you MUST set AGL_SECRET_KEY to a strong random value.\n"
            '   Generate one with: python -c "import secrets; print(secrets.token_hex(64))"\n'
        )
        sys.exit(1)

    # Development: persist key to file so tokens survive restarts
    key_file = Path(__file__).resolve().parent.parent.parent / "data" / ".secret_key"
    key_file.parent.mkdir(parents=True, exist_ok=True)
    if key_file.exists():
        return key_file.read_text().strip()
    key = secrets.token_hex(64)
    key_file.write_text(key)
    print(f"🔑 Development secret key persisted to {key_file}")
    return key


SECRET_KEY = _resolve_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.environ.get("AGL_TOKEN_HOURS", "24"))

# ── Password hashing ──────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Security schemes ──────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ═══════════════════════════════════════════════════════════
#  Password utilities
# ═══════════════════════════════════════════════════════════


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ═══════════════════════════════════════════════════════════
#  JWT utilities
# ═══════════════════════════════════════════════════════════


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ═══════════════════════════════════════════════════════════
#  API Key utilities
# ═══════════════════════════════════════════════════════════


def generate_api_key() -> str:
    """Generate a prefixed API key: agl_sk_..."""
    return f"agl_sk_{secrets.token_hex(24)}"


# ═══════════════════════════════════════════════════════════
#  FastAPI Dependencies
# ═══════════════════════════════════════════════════════════


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    api_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db),
) -> User:
    """
    Authenticate via JWT Bearer token OR X-API-Key header.
    Returns the User object or raises 401.
    """
    # Try JWT first
    if credentials and credentials.credentials:
        payload = decode_token(credentials.credentials)
        if payload and "sub" in payload:
            user = db.query(User).filter(User.id == payload["sub"]).first()
            if user and user.is_active:
                return user

    # Try API Key
    if api_key:
        key_obj = (
            db.query(APIKey)
            .filter(
                APIKey.key == api_key,
                APIKey.is_active == True,
            )
            .first()
        )
        if key_obj:
            key_obj.last_used = datetime.datetime.utcnow()
            db.commit()
            if key_obj.user and key_obj.user.is_active:
                return key_obj.user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="غير مصرح — Invalid or missing credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    api_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Same as get_current_user but returns None instead of raising 401.
    Used for pages that work with or without login.
    """
    try:
        return await get_current_user(credentials, api_key, db)
    except HTTPException:
        return None


# ═══════════════════════════════════════════════════════════
#  WebSocket Authentication
# ═══════════════════════════════════════════════════════════


async def verify_ws_token(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
) -> Optional[str]:
    """
    Verify JWT token passed as query parameter for WebSocket.
    Usage: ws://host/ws/scan/{id}?token=<jwt>
    Returns user_id if valid, None otherwise.
    """
    if not token:
        return None
    payload = decode_token(token)
    if payload and "sub" in payload:
        return payload["sub"]
    return None
