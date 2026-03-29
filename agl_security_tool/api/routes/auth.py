"""
AGL Security — Auth Routes
مسارات المصادقة — تسجيل دخول / تسجيل حساب / مفاتيح API
"""

import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..database import get_db, User, APIKey, _uuid
from ..auth import (
    hash_password,
    verify_password,
    create_access_token,
    generate_api_key,
    get_current_user,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ── Request / Response schemas ─────────────────────────────


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


class APIKeyResponse(BaseModel):
    key: str
    label: str
    created_at: str


class APIKeyCreateRequest(BaseModel):
    label: str = "default"


class UserProfile(BaseModel):
    id: str
    email: str
    username: str
    is_admin: bool
    created_at: str
    api_keys_count: int
    scans_count: int


# ── Routes ─────────────────────────────────────────────────


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """تسجيل حساب جديد — Register new account."""
    # Check duplicate
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="البريد مسجل مسبقاً — Email already registered"
        )

    user = User(
        id=_uuid(),
        email=req.email,
        username=req.username,
        hashed_pw=hash_password(req.password),
    )
    db.add(user)

    # Auto-create a default API key
    key = APIKey(id=_uuid(), key=generate_api_key(), label="default", user_id=user.id)
    db.add(key)
    db.commit()

    token = create_access_token(user.id, user.email)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """تسجيل الدخول — Login."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_pw):
        raise HTTPException(
            status_code=401, detail="بريد أو كلمة مرور خاطئة — Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="الحساب معطل — Account disabled")

    user.last_login = datetime.datetime.utcnow()
    db.commit()

    token = create_access_token(user.id, user.email)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
    )


@router.get("/me", response_model=UserProfile)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """الملف الشخصي — User profile."""
    return UserProfile(
        id=user.id,
        email=user.email,
        username=user.username,
        is_admin=user.is_admin,
        created_at=user.created_at.isoformat() if user.created_at else "",
        api_keys_count=len(user.api_keys),
        scans_count=len(user.scans),
    )


@router.post("/api-key", response_model=APIKeyResponse, status_code=201)
def create_api_key(
    req: APIKeyCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """إنشاء مفتاح API جديد — Create new API key."""
    key = APIKey(id=_uuid(), key=generate_api_key(), label=req.label, user_id=user.id)
    db.add(key)
    db.commit()
    return APIKeyResponse(
        key=key.key,
        label=key.label,
        created_at=key.created_at.isoformat() if key.created_at else "",
    )


@router.get("/api-keys")
def list_api_keys(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """قائمة مفاتيح API — List API keys."""
    keys = db.query(APIKey).filter(APIKey.user_id == user.id).all()
    return [
        {
            "id": k.id,
            "key": k.key[:12] + "..." + k.key[-4:],  # masked
            "label": k.label,
            "is_active": k.is_active,
            "created_at": k.created_at.isoformat() if k.created_at else "",
            "last_used": k.last_used.isoformat() if k.last_used else None,
        }
        for k in keys
    ]


@router.delete("/api-key/{key_id}")
def revoke_api_key(
    key_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """إلغاء مفتاح API — Revoke API key."""
    key = (
        db.query(APIKey).filter(APIKey.id == key_id, APIKey.user_id == user.id).first()
    )
    if not key:
        raise HTTPException(status_code=404, detail="مفتاح غير موجود — Key not found")
    key.is_active = False
    db.commit()
    return {"status": "revoked", "id": key_id}
