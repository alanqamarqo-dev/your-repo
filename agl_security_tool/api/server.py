"""
AGL Security — FastAPI Server
الخادم الرئيسي — FastAPI + Jinja2 + WebSocket

Run:
    uvicorn agl_security_tool.api.server:app --reload --port 8000

    # or from project root:
    python -m agl_security_tool.api.server
"""

import os
import json
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    _HAS_SLOWAPI = True
except ImportError:
    _HAS_SLOWAPI = False

from .database import init_db, get_db, Scan, User
from .auth import get_optional_user, verify_ws_token
from .routes import auth as auth_routes
from .routes import scan as scan_routes
from .routes import report as report_routes
from .routes import layer as layer_routes

# ── Paths ──────────────────────────────────────────────────
_API_DIR = Path(__file__).resolve().parent
_TEMPLATE_DIR = _API_DIR / "templates"
_STATIC_DIR = _API_DIR / "static"

# ── Environment ────────────────────────────────────────────
_AGL_ENV = os.environ.get("AGL_ENV", "development")
_IS_PRODUCTION = _AGL_ENV == "production"


# ═══════════════════════════════════════════════════════════
#  Security Headers Middleware
# ═══════════════════════════════════════════════════════════


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        if _IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        return response


# ── Lifespan ───────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and pre-warm scan engine on startup."""
    init_db()
    env_label = "🔴 PRODUCTION" if _IS_PRODUCTION else "🟢 DEVELOPMENT"
    print(f"🛡️  AGL Security API — {env_label}")
    print(f"🛡️  SQLite database initialized")

    # Initialize MongoDB
    try:
        from .database_mongo import (
            init_mongo_db,
            is_mongo_available,
            migrate_from_sqlite,
        )

        if init_mongo_db():
            print("🍃 MongoDB: CONNECTED")
            # Auto-migrate existing SQLite data to MongoDB
            try:
                migrate_from_sqlite()
            except Exception as e:
                print(f"⚠️   SQLite→MongoDB migration: {e}")
        else:
            print("⚠️   MongoDB: NOT AVAILABLE (using SQLite only)")
    except Exception as e:
        print(f"⚠️   MongoDB init error: {e}")
    if _HAS_SLOWAPI:
        print("🛡️  Rate limiting: ENABLED")
    else:
        print("⚠️   Rate limiting: DISABLED (install slowapi)")

    # Pre-warm the scan engine in a background thread so first scan is fast
    import threading

    def _prewarm():
        try:
            from .routes.scan import _get_audit_engine

            engine = _get_audit_engine()
            if engine:
                print("🛡️  Scan engine: READY")
            else:
                print("⚠️   Scan engine: FAILED to initialize")
        except Exception as e:
            print(f"⚠️   Scan engine prewarm error: {e}")

        # Also pre-warm the full audit engines (Layer 6+7)
        try:
            from .full_audit import _get_full_engines

            engines = _get_full_engines()
            count = len(engines)
            print(f"🛡️  Full audit engines: {count} loaded (Layer 0-7)")
        except Exception as e:
            print(f"⚠️   Full audit engines prewarm error: {e}")

    threading.Thread(target=_prewarm, daemon=True).start()

    print(f"📂 Templates: {_TEMPLATE_DIR}")
    print(f"🌐 Open http://localhost:8000")
    yield
    print("🛡️  AGL Security API — Shutting down")


# ── App ────────────────────────────────────────────────────
app = FastAPI(
    title="AGL Security API",
    description="🛡️ أداة تحليل أمان العقود الذكية — Smart Contract Security Analysis — Full 7-Layer Audit",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if not _IS_PRODUCTION else None,  # Disable Swagger in prod
    redoc_url="/api/redoc" if not _IS_PRODUCTION else None,
)

# ── Security Middleware ────────────────────────────────────

# 1. Security Headers (applied to every response)
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS — restricted by environment variable
_CORS_ORIGINS = os.environ.get("AGL_CORS_ORIGINS", "*").split(",")
_CORS_ORIGINS = [o.strip() for o in _CORS_ORIGINS if o.strip()]

if _IS_PRODUCTION and _CORS_ORIGINS == ["*"]:
    print("⚠️  WARNING: CORS is open (allow_origins=*) in production!")
    print("   Set AGL_CORS_ORIGINS=https://yourdomain.com")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "Accept"],
)

# 3. Trusted Host (production only)
_TRUSTED_HOSTS = os.environ.get("AGL_TRUSTED_HOSTS", "")
if _TRUSTED_HOSTS:
    hosts = [h.strip() for h in _TRUSTED_HOSTS.split(",") if h.strip()]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)

# 4. Rate Limiting
if _HAS_SLOWAPI:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200/minute"],  # Global default
        storage_uri=os.environ.get("AGL_REDIS_URL", "memory://"),
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Static files
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

# Include API routes
app.include_router(auth_routes.router)
app.include_router(scan_routes.router)
app.include_router(report_routes.router)
app.include_router(layer_routes.router)


# ═══════════════════════════════════════════════════════════
#  WebSocket — Real-time scan progress
# ═══════════════════════════════════════════════════════════


class ConnectionManager:
    """Manages WebSocket connections for scan progress."""

    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}  # scan_id → [websockets]

    async def connect(self, websocket: WebSocket, scan_id: str):
        await websocket.accept()
        if scan_id not in self.active:
            self.active[scan_id] = []
        self.active[scan_id].append(websocket)

    def disconnect(self, websocket: WebSocket, scan_id: str):
        if scan_id in self.active:
            self.active[scan_id] = [
                ws for ws in self.active[scan_id] if ws != websocket
            ]

    async def broadcast(self, scan_id: str, data: dict):
        if scan_id in self.active:
            for ws in self.active[scan_id]:
                try:
                    await ws.send_json(data)
                except Exception:
                    pass


ws_manager = ConnectionManager()


@app.websocket("/ws/scan/{scan_id}")
async def ws_scan_progress(
    websocket: WebSocket,
    scan_id: str,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time scan progress.
    Requires JWT token as query parameter: ws://host/ws/scan/{id}?token=<jwt>
    In development mode, unauthenticated connections are allowed.
    """
    # Verify authentication
    user_id = await verify_ws_token(websocket, token)
    if not user_id and _IS_PRODUCTION:
        await websocket.close(code=4001, reason="Authentication required")
        return

    await ws_manager.connect(websocket, scan_id)
    try:
        while True:
            # Client can send ping to keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, scan_id)


# ═══════════════════════════════════════════════════════════
#  Web Pages (HTML Templates)
# ═══════════════════════════════════════════════════════════


@app.get("/", response_class=HTMLResponse)
async def page_index(request: Request):
    """الواجهة الرئيسية — ChatGPT-style SPA."""
    return templates.TemplateResponse("app.html", {"request": request})


@app.get("/classic", response_class=HTMLResponse)
async def page_classic(request: Request):
    """الصفحة الكلاسيكية — Classic landing page (legacy)."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def page_login(request: Request):
    """صفحة تسجيل الدخول — Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def page_dashboard(request: Request):
    """لوحة التحكم — Dashboard (scan history)."""
    return templates.TemplateResponse("history.html", {"request": request})


@app.get("/scan/{scan_id}/progress", response_class=HTMLResponse)
async def page_scan_progress(request: Request, scan_id: str):
    """صفحة تقدم الفحص — Scan progress page."""
    return templates.TemplateResponse(
        "scan.html", {"request": request, "scan_id": scan_id}
    )


@app.get("/scan/{scan_id}/results", response_class=HTMLResponse)
async def page_results(request: Request, scan_id: str):
    """لوحة النتائج — Results dashboard."""
    return templates.TemplateResponse(
        "results.html", {"request": request, "scan_id": scan_id}
    )


# ═══════════════════════════════════════════════════════════
#  Health check
# ═══════════════════════════════════════════════════════════


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "AGL Security API",
        "version": "2.0.0",
        "environment": _AGL_ENV,
        "rate_limiting": _HAS_SLOWAPI,
    }


# ═══════════════════════════════════════════════════════════
#  Run directly
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("AGL_API_PORT", "8000"))
    uvicorn.run(
        "agl_security_tool.api.server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
