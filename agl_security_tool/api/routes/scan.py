"""
AGL Security — Scan Routes
مسارات الفحص — رفع ملف / رابط GitHub / مشروع ZIP / تدقيق كامل

POST /api/v1/scan                → Upload .sol file, quick/deep scan (core engine)
POST /api/v1/scan/url            → Git-clone GitHub URL → full 7-layer audit
POST /api/v1/scan/project        → Upload ZIP project → full 7-layer audit
POST /api/v1/scan/full           → Upload .sol file → full 7-layer audit (all engines)
GET  /api/v1/scan/{id}           → Get scan status + results
GET  /api/v1/scan/{id}/report    → Get Markdown report
GET  /api/v1/scans               → List user's scans
DELETE /api/v1/scan/{id}         → Delete scan
"""

import os
import time
import datetime
import traceback
import tempfile
import shutil
import threading
import logging
import zipfile
from pathlib import Path
from typing import Optional, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db, get_db_session, Scan, User, _uuid, _now
from ..auth import get_current_user

_logger = logging.getLogger("AGL.api.scan")

router = APIRouter(prefix="/api/v1", tags=["Scan"])

# ── Upload directory ───────────────────────────────────────
_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── Scan timeout (seconds) ─────────────────────────────────
_SCAN_TIMEOUT = int(os.environ.get("AGL_SCAN_TIMEOUT", "300"))  # 5 min default

# ── Pre-initialized engine singleton ───────────────────────
_audit_engine = None
_engine_lock = threading.Lock()
_engine_init_error: Optional[str] = None


def _get_audit_engine():
    """Get or create the singleton AGLSecurityAudit engine.
    Thread-safe lazy initialization — engine loads once, reused across scans."""
    global _audit_engine, _engine_init_error
    if _audit_engine is not None:
        return _audit_engine
    with _engine_lock:
        if _audit_engine is not None:
            return _audit_engine
        try:
            _logger.info("Initializing AGLSecurityAudit engine (first scan)...")
            from agl_security_tool import AGLSecurityAudit

            _audit_engine = AGLSecurityAudit()
            _logger.info("AGLSecurityAudit engine ready")
        except Exception as e:
            _engine_init_error = f"{type(e).__name__}: {e}"
            _logger.error("Failed to init AGLSecurityAudit: %s", e)
    return _audit_engine


# ── Schemas ────────────────────────────────────────────────


class ScanURLRequest(BaseModel):
    url: str
    mode: str = "full"  # quick | deep | full (default changed to full)
    branch: str = ""  # empty = default branch
    skip_heikal: bool = False
    include_deps: bool = False
    include_tests: bool = False


class ScanSummary(BaseModel):
    id: str
    target_name: str
    target_type: str
    scan_mode: str
    status: str
    progress: int
    current_layer: str
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    security_score: float
    heikal_xi: Optional[float] = None
    total_attacks: int
    profitable_attacks: int
    max_profit_usd: float
    created_at: str
    duration_sec: float
    error_message: Optional[str] = None
    project_type: Optional[str] = None
    contracts_scanned: Optional[int] = None
    layers_used: Optional[List[str]] = None


# ── Background scan worker ─────────────────────────────────


def _run_scan_with_timeout(audit, target_path: str, mode: str, timeout: int):
    """Run scan in a sub-thread with timeout protection."""
    result_holder = [None]
    error_holder = [None]

    def _inner():
        try:
            if mode == "quick":
                result_holder[0] = audit.quick_scan(target_path)
            elif mode == "scan":
                result_holder[0] = audit.scan(target_path)
            else:
                result_holder[0] = audit.deep_scan(target_path)
        except Exception as e:
            error_holder[0] = e

    t = threading.Thread(target=_inner, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        raise TimeoutError(
            f"Scan timed out after {timeout}s — try 'quick' mode for faster results"
        )
    if error_holder[0]:
        raise error_holder[0]
    return result_holder[0]


def _run_scan_background(scan_id: str, target_path: str, mode: str):
    """
    Run the actual AGL security scan in a background thread.
    Uses a pre-initialized singleton engine and enforces a timeout.
    """
    db = get_db_session()
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        db.close()
        return

    try:
        scan.status = "running"
        scan.started_at = _now()
        scan.progress = 5
        scan.current_layer = "Loading engines..."
        db.commit()

        # Use pre-initialized singleton engine
        audit = _get_audit_engine()
        if audit is None:
            raise RuntimeError(
                f"Scan engine failed to initialize: {_engine_init_error or 'unknown'}"
            )

        scan.progress = 10
        scan.current_layer = "Layer 0: Preprocessing"
        db.commit()

        # Run scan with timeout protection
        timeout = _SCAN_TIMEOUT if mode != "quick" else min(_SCAN_TIMEOUT, 60)
        t0 = time.time()
        result = _run_scan_with_timeout(audit, target_path, mode, timeout)
        elapsed = time.time() - t0

        # Parse results
        findings = result.get("findings", [])

        sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in findings:
            sev = f.get("severity", "LOW").upper()
            if sev in sev_counts:
                sev_counts[sev] += 1

        total = len(findings)

        # Security score: 100 minus weighted deductions
        score = max(
            0,
            100
            - sev_counts["CRITICAL"] * 15
            - sev_counts["HIGH"] * 8
            - sev_counts["MEDIUM"] * 3
            - sev_counts["LOW"] * 1,
        )

        # Attack simulation data
        attacks = result.get("attack_simulations", [])
        profitable = [a for a in attacks if a.get("is_profitable")]

        # Heikal math data
        heikal = result.get("heikal_analysis", {})

        # Update scan record
        scan.status = "completed"
        scan.progress = 100
        scan.current_layer = "Done"
        scan.completed_at = _now()
        scan.duration_sec = round(elapsed, 2)
        scan.total_findings = total
        scan.critical_count = sev_counts["CRITICAL"]
        scan.high_count = sev_counts["HIGH"]
        scan.medium_count = sev_counts["MEDIUM"]
        scan.low_count = sev_counts["LOW"]
        scan.security_score = score
        scan.total_attacks = len(attacks)
        scan.profitable_attacks = len(profitable)
        scan.max_profit_usd = max(
            (a.get("net_profit_usd", 0) for a in attacks), default=0
        )
        scan.result_json = result

        # Heikal scores
        if heikal:
            scan.heikal_xi = heikal.get("composite_xi")
            scan.heikal_wave = heikal.get("wave_score")
            scan.heikal_tunnel = heikal.get("tunneling_score")
            scan.heikal_holo = heikal.get("holographic_score")
            scan.heikal_resonance = heikal.get("resonance_score")

        db.commit()

    except Exception as exc:
        scan.status = "failed"
        scan.error_message = f"{type(exc).__name__}: {exc}"
        scan.progress = 0
        scan.completed_at = _now()
        db.commit()
        traceback.print_exc()

    finally:
        db.close()


# ── Routes ─────────────────────────────────────────────────


@router.post("/scan", response_model=ScanSummary, status_code=202)
async def upload_and_scan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: str = Form("deep"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    رفع ملف .sol وبدء الفحص — Upload .sol file and start scan.
    Returns immediately; scan runs in background.
    Max file size: 5 MB.
    """
    # ── Validation ──
    if not file.filename.endswith(".sol"):
        raise HTTPException(400, "يجب رفع ملف .sol — Only .sol files accepted")

    if mode not in ("quick", "scan", "deep"):
        mode = "deep"

    # ── File size limit (5 MB) ──
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            413,
            f"الملف كبير جداً ({len(content) / 1024 / 1024:.1f} MB) — "
            f"Max file size is {MAX_FILE_SIZE / 1024 / 1024:.0f} MB",
        )

    # ── Filename sanitization ──
    import re as _re_scan

    safe_filename = _re_scan.sub(r"[^\w.\-]", "_", file.filename)
    if not safe_filename.endswith(".sol"):
        safe_filename += ".sol"

    # Save uploaded file
    scan_id = _uuid()
    target_dir = _UPLOAD_DIR / scan_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_filename

    target_path.write_bytes(content)

    # Create scan record
    scan = Scan(
        id=scan_id,
        user_id=user.id,
        target_name=file.filename,
        target_type="file",
        scan_mode=mode,
        status="pending",
    )
    db.add(scan)
    db.commit()

    # Start background scan
    background_tasks.add_task(_run_scan_background, scan_id, str(target_path), mode)

    return _scan_to_summary(scan)


@router.post("/scan/url", response_model=ScanSummary, status_code=202)
async def scan_from_url(
    req: ScanURLRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    فحص من رابط GitHub — Full 7-layer audit from GitHub URL.
    Clones the repo, discovers project structure, runs all layers.
    """
    from ..full_audit import is_git_url

    if not is_git_url(req.url) and not req.url.endswith(".sol"):
        raise HTTPException(
            400, "يجب أن يكون رابط GitHub أو Git — Must be a GitHub/Git URL"
        )

    scan_id = _uuid()

    scan = Scan(
        id=scan_id,
        user_id=user.id,
        target_name=req.url,
        target_type="url",
        scan_mode=req.mode,
        status="pending",
    )
    db.add(scan)
    db.commit()

    # Use full audit pipeline (with git clone + all layers)
    from ..full_audit import run_full_audit_background

    background_tasks.add_task(
        run_full_audit_background,
        scan_id=scan_id,
        target=req.url,
        mode=req.mode,
        branch=req.branch or None,
        skip_heikal=req.skip_heikal,
        include_deps=req.include_deps,
        include_tests=req.include_tests,
    )

    return _scan_to_summary(scan)


@router.post("/scan/project", response_model=ScanSummary, status_code=202)
async def upload_project_scan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: str = Form("full"),
    skip_heikal: bool = Form(False),
    include_deps: bool = Form(False),
    include_tests: bool = Form(False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    رفع مشروع ZIP وبدء التدقيق الكامل — Upload ZIP project for full 7-layer audit.
    Accepts .zip files containing Solidity project (Foundry/Hardhat/Truffle/Bare).
    Max ZIP size: 50 MB.
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "يجب رفع ملف .zip — Only .zip files accepted")

    MAX_ZIP_SIZE = 50 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_ZIP_SIZE:
        raise HTTPException(
            413,
            f"الملف كبير جداً ({len(content) / 1024 / 1024:.1f} MB) — "
            f"Max ZIP size is {MAX_ZIP_SIZE / 1024 / 1024:.0f} MB",
        )

    # Validate it's a real ZIP
    if not zipfile.is_zipfile(__import__("io").BytesIO(content)):
        raise HTTPException(400, "الملف ليس ZIP صالح — Invalid ZIP file")

    scan_id = _uuid()
    target_dir = _UPLOAD_DIR / scan_id
    target_dir.mkdir(parents=True, exist_ok=True)

    # Extract ZIP
    from ..full_audit import extract_zip_project

    try:
        project_path = extract_zip_project(content, str(target_dir))
    except ValueError as e:
        raise HTTPException(400, f"خطأ في الملف — {e}")
    except Exception as e:
        raise HTTPException(500, f"فشل استخراج الملف — Failed to extract: {e}")

    scan = Scan(
        id=scan_id,
        user_id=user.id,
        target_name=file.filename,
        target_type="project",
        scan_mode=mode,
        status="pending",
    )
    db.add(scan)
    db.commit()

    from ..full_audit import run_full_audit_background

    background_tasks.add_task(
        run_full_audit_background,
        scan_id=scan_id,
        target=project_path,
        mode=mode,
        skip_heikal=skip_heikal,
        include_deps=include_deps,
        include_tests=include_tests,
    )

    return _scan_to_summary(scan)


@router.post("/scan/full", response_model=ScanSummary, status_code=202)
async def upload_and_full_scan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: str = Form("full"),
    skip_heikal: bool = Form(False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    رفع ملف .sol وبدء التدقيق الكامل 7 طبقات — Upload .sol file for full 7-layer audit.
    Unlike /scan (core-only), this runs Layer 6 (Exploit Reasoning) + Layer 7 (Heikal Math).
    Max file size: 5 MB.
    """
    if not file.filename.endswith(".sol"):
        raise HTTPException(400, "يجب رفع ملف .sol — Only .sol files accepted")

    MAX_FILE_SIZE = 5 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            413,
            f"الملف كبير جداً ({len(content) / 1024 / 1024:.1f} MB) — "
            f"Max file size is {MAX_FILE_SIZE / 1024 / 1024:.0f} MB",
        )

    import re as _re_scan

    safe_filename = _re_scan.sub(r"[^\w.\-]", "_", file.filename)
    if not safe_filename.endswith(".sol"):
        safe_filename += ".sol"

    scan_id = _uuid()
    target_dir = _UPLOAD_DIR / scan_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_filename
    target_path.write_bytes(content)

    scan = Scan(
        id=scan_id,
        user_id=user.id,
        target_name=file.filename,
        target_type="file",
        scan_mode=mode,
        status="pending",
    )
    db.add(scan)
    db.commit()

    from ..full_audit import run_full_audit_background

    background_tasks.add_task(
        run_full_audit_background,
        scan_id=scan_id,
        target=str(target_path),
        mode=mode,
        skip_heikal=skip_heikal,
    )

    return _scan_to_summary(scan)


@router.get("/scan/{scan_id}")
def get_scan(
    scan_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """حالة الفحص + النتائج — Scan status + results."""
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user.id).first()
    if not scan:
        raise HTTPException(404, "فحص غير موجود — Scan not found")

    data = _scan_to_summary(scan)
    # Include full results if completed
    if scan.status == "completed" and scan.result_json:
        return {**data.dict(), "result": scan.result_json}
    return data


@router.get("/scan/{scan_id}/report")
def get_scan_report(
    scan_id: str,
    format: str = "markdown",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    تقرير التدقيق بصيغة Markdown — Get audit report in Markdown format.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user.id).first()
    if not scan:
        raise HTTPException(404, "فحص غير موجود — Scan not found")
    if scan.status != "completed":
        raise HTTPException(400, "الفحص لم يكتمل بعد — Scan not completed yet")
    if not scan.result_json:
        raise HTTPException(404, "لا توجد نتائج — No results available")

    if format == "markdown":
        from ..full_audit import generate_markdown_report

        md = generate_markdown_report(scan.result_json)
        from fastapi.responses import PlainTextResponse

        return PlainTextResponse(
            content=md,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="audit_{scan_id[:8]}.md"'
            },
        )

    # Default: JSON
    return scan.result_json


@router.get("/scans")
def list_scans(
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """قائمة الفحوصات — List user's scans."""
    scans = (
        db.query(Scan)
        .filter(Scan.user_id == user.id)
        .order_by(Scan.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(Scan).filter(Scan.user_id == user.id).count()
    return {
        "total": total,
        "scans": [_scan_to_summary(s).dict() for s in scans],
    }


@router.delete("/scan/{scan_id}")
def delete_scan(
    scan_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """حذف فحص — Delete scan."""
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user.id).first()
    if not scan:
        raise HTTPException(404, "فحص غير موجود — Scan not found")

    # Remove uploaded files
    target_dir = _UPLOAD_DIR / scan_id
    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)

    db.delete(scan)
    db.commit()
    return {"status": "deleted", "id": scan_id}


@router.get("/stats")
def user_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """إحصائيات المستخدم — User statistics."""
    scans = db.query(Scan).filter(Scan.user_id == user.id).all()
    completed = [s for s in scans if s.status == "completed"]

    total_findings = sum(s.total_findings for s in completed)
    total_critical = sum(s.critical_count for s in completed)
    avg_score = (
        sum(s.security_score for s in completed) / len(completed) if completed else 0
    )

    return {
        "total_scans": len(scans),
        "completed_scans": len(completed),
        "total_findings": total_findings,
        "total_critical": total_critical,
        "average_score": round(avg_score, 1),
        "latest_scan": _scan_to_summary(scans[0]).dict() if scans else None,
    }


# ── Helper ─────────────────────────────────────────────────


def _scan_to_summary(scan: Scan) -> ScanSummary:
    # Extract extra info from result_json if available
    project_type = None
    contracts_scanned = None
    layers_used = None
    if scan.result_json and isinstance(scan.result_json, dict):
        project_type = scan.result_json.get("project_type")
        contracts_scanned = scan.result_json.get("contracts_scanned")
        layers_used = scan.result_json.get("layers_used")

    return ScanSummary(
        id=scan.id,
        target_name=scan.target_name,
        target_type=scan.target_type,
        scan_mode=scan.scan_mode,
        status=scan.status,
        progress=scan.progress,
        current_layer=scan.current_layer or "",
        total_findings=scan.total_findings,
        critical_count=scan.critical_count,
        high_count=scan.high_count,
        medium_count=scan.medium_count,
        low_count=scan.low_count,
        security_score=scan.security_score,
        heikal_xi=scan.heikal_xi,
        total_attacks=scan.total_attacks,
        profitable_attacks=scan.profitable_attacks,
        max_profit_usd=scan.max_profit_usd,
        created_at=scan.created_at.isoformat() if scan.created_at else "",
        duration_sec=scan.duration_sec,
        error_message=scan.error_message,
        project_type=project_type,
        contracts_scanned=contracts_scanned,
        layers_used=layers_used,
    )
