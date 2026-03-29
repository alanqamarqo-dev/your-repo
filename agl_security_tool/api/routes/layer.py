"""
AGL Security — Per-Layer Scan Routes
مسارات الفحص لكل طبقة — يمكن تشغيل كل طبقة على حدة

POST /api/v1/layer/scan          → Run specific layer(s) on uploaded code
GET  /api/v1/layer/engines       → List available engines/layers
POST /api/v1/layer/quick-test    → Quick engine health check

Layers available:
  L0     — Flattener (AST preprocessing)
  L0.5   — Z3 Symbolic Execution
  L1-L4  — State Extraction
  L5     — Detectors + Parser
  L6     — Exploit Reasoning
  L7     — Heikal Mathematics
  full   — All layers (L0 → L7)
"""

import os
import time
import datetime
import threading
import traceback
import tempfile
import logging
import concurrent.futures
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from ..auth import get_current_user
from ..database_mongo import (
    create_scan,
    get_scan,
    update_scan,
    MongoScan,
    is_mongo_available,
)

_logger = logging.getLogger("AGL.api.layer")

router = APIRouter(prefix="/api/v1/layer", tags=["Layer Scan"])

# ── Concurrency limiter — only 1 deep scan at a time ──────
_SCAN_SEMAPHORE = threading.Semaphore(1)

# ── Per-layer timeout (seconds) ───────────────────────────
_LAYER_TIMEOUT = {
    "L0": 300,      # Core deep scan: max 5 minutes
    "L0.5": 60,     # Z3: max 1 minute
    "L1-L4": 60,    # State extraction: 1 minute
    "L5": 60,       # Detectors: 1 minute
    "L6": 120,      # Exploit reasoning: 2 minutes
    "L7": 30,       # Heikal math: 30 seconds
}


def _run_with_timeout(func, timeout_sec, *args, **kwargs):
    """Run a function with a timeout. Returns result or raises TimeoutError."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_sec)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(
                f"Layer timed out after {timeout_sec}s"
            )

# ── Upload directory ───────────────────────────────────────
_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── Layer definitions ──────────────────────────────────────
LAYER_INFO = {
    "L0": {
        "name": "Flattener",
        "name_ar": "مُسطّح الكود",
        "description": "AST preprocessing & inheritance flattening",
        "description_ar": "معالجة شجرة التحليل وتسطيح الوراثة",
        "icon": "🔧",
        "color": "#6366f1",
    },
    "L0.5": {
        "name": "Z3 Symbolic",
        "name_ar": "Z3 رمزي",
        "description": "Z3 SMT solver — formal verification of constraints",
        "description_ar": "محرك Z3 — التحقق الرسمي من القيود",
        "icon": "🧮",
        "color": "#8b5cf6",
    },
    "L1-L4": {
        "name": "State Extraction",
        "name_ar": "استخراج الحالة",
        "description": "Multi-layer state extraction & data flow analysis",
        "description_ar": "استخراج الحالة متعدد الطبقات وتحليل تدفق البيانات",
        "icon": "📊",
        "color": "#a855f7",
    },
    "L5": {
        "name": "Detectors",
        "name_ar": "الكاشفات",
        "description": "22 vulnerability detectors + pattern matching",
        "description_ar": "22 كاشف ثغرات + مطابقة الأنماط",
        "icon": "🔍",
        "color": "#ec4899",
    },
    "L6": {
        "name": "Exploit Reasoning",
        "name_ar": "تحليل الاستغلال",
        "description": "Attack chain construction & profitability analysis",
        "description_ar": "بناء سلاسل الهجوم وتحليل الربحية",
        "icon": "💀",
        "color": "#ef4444",
    },
    "L7": {
        "name": "Heikal Mathematics",
        "name_ar": "رياضيات هيكل",
        "description": "Quantum tunneling, wave analysis, holographic & resonance scoring",
        "description_ar": "النفق الكمي، تحليل الموجات، التصوير المجسم والرنين",
        "icon": "🌀",
        "color": "#06b6d4",
    },
}


# ── Schemas ────────────────────────────────────────────────


class LayerScanRequest(BaseModel):
    """Request schema for per-layer scan."""

    layers: List[str] = ["full"]  # e.g. ["L0", "L5", "L7"] or ["full"]


class LayerScanResponse(BaseModel):
    scan_id: str
    status: str
    layers_requested: List[str]
    message: str


class EngineInfo(BaseModel):
    layer: str
    name: str
    name_ar: str
    description: str
    description_ar: str
    icon: str
    color: str
    available: bool


# ── Engine Loading ─────────────────────────────────────────
_full_engines: Optional[Dict] = None
_engines_lock = threading.Lock()


def _get_engines() -> Dict:
    """Get or initialize the full audit engines (singleton)."""
    global _full_engines
    if _full_engines is not None:
        return _full_engines
    with _engines_lock:
        if _full_engines is not None:
            return _full_engines
        try:
            from ..full_audit import _get_full_engines

            _full_engines = _get_full_engines()
            return _full_engines
        except Exception as e:
            _logger.error(f"Failed to load engines: {e}")
            return {}


# ═══════════════════════════════════════════════════════════
#  GET /layer/engines — List available layers
# ═══════════════════════════════════════════════════════════


@router.get("/engines", response_model=List[EngineInfo])
def list_engines(user=Depends(get_current_user)):
    """List all available scan layers/engines."""
    engines = _get_engines()
    result = []
    for layer_key, info in LAYER_INFO.items():
        # Check which engines this layer needs
        available = True
        if layer_key == "L0":
            available = "flattener" in engines
        elif layer_key == "L0.5":
            available = "z3_prover" in engines
        elif layer_key == "L1-L4":
            available = "state_extractor" in engines
        elif layer_key == "L5":
            available = "detectors" in engines or "parser" in engines
        elif layer_key == "L6":
            available = "exploit_engine" in engines
        elif layer_key == "L7":
            available = any(
                k in engines
                for k in [
                    "heikal_tunnel",
                    "heikal_wave",
                    "heikal_holo",
                    "heikal_resonance",
                ]
            )
        result.append(
            EngineInfo(
                layer=layer_key,
                available=available,
                **info,
            )
        )
    return result


# ═══════════════════════════════════════════════════════════
#  POST /layer/scan — Run specific layers
# ═══════════════════════════════════════════════════════════


@router.post("/scan", response_model=LayerScanResponse)
async def layer_scan(
    file: UploadFile = File(...),
    layers: str = Form("full"),  # comma-separated: "L0,L5,L7" or "full"
    user=Depends(get_current_user),
):
    """
    Run specific scan layers on an uploaded Solidity file.

    Layers: L0, L0.5, L1-L4, L5, L6, L7, or "full" for all.
    Separate multiple layers with commas: "L0,L5,L7"
    """
    # Validate file
    if not file.filename:
        raise HTTPException(400, "No file uploaded")

    fname = file.filename.lower()
    if not fname.endswith(".sol"):
        raise HTTPException(400, "Only .sol files are supported")

    # Parse layers
    layer_list = [l.strip() for l in layers.split(",") if l.strip()]
    if "full" in layer_list:
        layer_list = list(LAYER_INFO.keys())

    # Validate layer names
    for l in layer_list:
        if l not in LAYER_INFO:
            raise HTTPException(
                400, f"Unknown layer: {l}. Valid: {list(LAYER_INFO.keys())}"
            )

    # Save uploaded file to scan-specific directory
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 5MB)")

    # Create scan record first to get scan_id for directory
    user_id = user.id if hasattr(user, "id") else str(user)
    scan = create_scan(
        user_id=user_id,
        target_name=file.filename,
        target_type="file",
        scan_mode=f"layers:{','.join(layer_list)}",
    )

    if not scan:
        raise HTTPException(500, "Failed to create scan record")

    scan_id = scan.id

    # Sanitize filename and save to isolated directory
    import re as _re

    safe_filename = _re.sub(r"[^\w.\-]", "_", file.filename)
    if not safe_filename.endswith(".sol"):
        safe_filename += ".sol"

    target_dir = _UPLOAD_DIR / scan_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_filename
    target_path.write_bytes(content)

    # Run scan in background
    thread = threading.Thread(
        target=_run_layer_scan_background,
        args=(scan_id, str(target_path), layer_list),
        daemon=True,
    )
    thread.start()

    layers_display = ", ".join(f"{LAYER_INFO[l]['icon']} {l}" for l in layer_list)
    return LayerScanResponse(
        scan_id=scan_id,
        status="running",
        layers_requested=layer_list,
        message=f"Scan started with layers: {layers_display}",
    )


# ═══════════════════════════════════════════════════════════
#  Background Layer Scan Worker
# ═══════════════════════════════════════════════════════════


def _run_layer_scan_background(scan_id: str, target_path: str, layers: List[str]):
    """Run selected layers sequentially in a background thread."""
    from ..full_audit import (
        _make_json_safe,
        run_core_deep_scan,
        run_z3_symbolic,
        run_state_extraction,
        run_detectors,
        run_exploit_reasoning,
        run_heikal_math,
        discover_project,
    )

    # Acquire semaphore so only one deep scan runs at a time
    acquired = _SCAN_SEMAPHORE.acquire(timeout=30)
    if not acquired:
        update_scan(
            scan_id,
            status="failed",
            error_message="Server busy — another scan is running. Try again shortly.",
            progress=100,
            current_layer="Queued",
            completed_at=datetime.datetime.utcnow(),
        )
        return

    try:
        _run_layer_scan_inner(
            scan_id, target_path, layers,
            _make_json_safe, run_core_deep_scan, run_z3_symbolic,
            run_state_extraction, run_detectors, run_exploit_reasoning,
            run_heikal_math, discover_project,
        )
    finally:
        _SCAN_SEMAPHORE.release()


def _run_layer_scan_inner(
    scan_id, target_path, layers,
    _make_json_safe, run_core_deep_scan, run_z3_symbolic,
    run_state_extraction, run_detectors, run_exploit_reasoning,
    run_heikal_math, discover_project,
):

    update_scan(scan_id, status="running", started_at=datetime.datetime.utcnow())
    t0 = time.time()

    try:
        engines = _get_engines()
        if not engines:
            raise RuntimeError("No engines available")

        # Resolve target: if it's a single .sol file, use parent dir
        target = Path(target_path).resolve()
        if target.is_file() and target.suffix == ".sol":
            project_dir = str(target.parent)
        elif target.is_dir():
            project_dir = str(target)
        else:
            raise FileNotFoundError(f"Target not found: {target_path}")

        # Discover project structure
        project = discover_project(project_dir)
        if not project.get("sol_files") and not project.get("contracts"):
            raise RuntimeError("No Solidity files found")

        total_layers = len(layers)
        all_findings = []
        layer_results = {}
        deep_scan_result = {}  # Store L0 result for L6
        attacks = []
        heikal_data = {}

        for i, layer in enumerate(layers):
            progress = int(((i) / total_layers) * 90) + 5
            update_scan(
                scan_id,
                progress=progress,
                current_layer=f"{LAYER_INFO[layer]['icon']} {LAYER_INFO[layer]['name']}",
            )

            try:
                timeout = _LAYER_TIMEOUT.get(layer, 120)

                if layer == "L0":
                    result = _run_with_timeout(
                        run_core_deep_scan, timeout, engines, project
                    )
                    deep_scan_result = result  # Save for L6
                    # result is dict keyed by contract name, each with findings
                    for contract_name, scan_data in result.items():
                        if isinstance(scan_data, dict):
                            # Check both 'all_findings_unified' and 'findings' keys
                            contract_findings = scan_data.get(
                                "all_findings_unified", scan_data.get("findings", [])
                            )
                            if isinstance(contract_findings, list):
                                for f in contract_findings:
                                    if isinstance(f, dict):
                                        f.setdefault("source_file", contract_name)
                                all_findings.extend(contract_findings)
                    layer_results["L0_deep_scan"] = _make_json_safe(result)

                elif layer == "L0.5":
                    z3_results = _run_with_timeout(
                        run_z3_symbolic, timeout, engines, project
                    )
                    all_findings.extend(z3_results)
                    layer_results["L0.5_z3_symbolic"] = _make_json_safe(z3_results)

                elif layer == "L1-L4":
                    state = _run_with_timeout(
                        run_state_extraction, timeout, engines, project
                    )
                    layer_results["L1_L4_state_extraction"] = _make_json_safe(state)

                elif layer == "L5":
                    det_results = _run_with_timeout(
                        run_detectors, timeout, engines, project
                    )
                    all_findings.extend(det_results)
                    layer_results["L5_detectors"] = _make_json_safe(det_results)

                elif layer == "L6":
                    # Pass deep_scan_result (dict keyed by contract) as expected
                    exploit_data = _run_with_timeout(
                        run_exploit_reasoning, timeout,
                        engines, project, deep_scan_results=deep_scan_result
                    )
                    # exploit_data is dict keyed by contract name
                    for cname, cdata in exploit_data.items():
                        if isinstance(cdata, dict):
                            proofs = cdata.get("exploit_proofs", [])
                            for p in proofs:
                                if isinstance(p, dict) and p.get("is_exploitable"):
                                    attacks.append(p)
                    layer_results["L6_exploit_reasoning"] = _make_json_safe(
                        exploit_data
                    )

                elif layer == "L7":
                    heikal_data = _run_with_timeout(
                        run_heikal_math, timeout, engines, project
                    )
                    layer_results["L7_heikal_math"] = _make_json_safe(heikal_data)

            except TimeoutError as te:
                _logger.warning(f"Layer {layer} timed out: {te}")
                layer_results[f"{layer}_timeout"] = str(te)
            except Exception as e:
                _logger.warning(f"Layer {layer} error: {e}")
                layer_results[f"{layer}_error"] = str(e)

        # Calculate severity counts
        sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in all_findings:
            sev = (f.get("severity") or "LOW").upper()
            if sev in sev_counts:
                sev_counts[sev] += 1

        total = len(all_findings)
        score = max(
            0,
            100
            - sev_counts["CRITICAL"] * 15
            - sev_counts["HIGH"] * 8
            - sev_counts["MEDIUM"] * 3
            - sev_counts["LOW"] * 1,
        )

        elapsed = time.time() - t0

        # Build result
        result_json = _make_json_safe(
            {
                "findings": all_findings,
                "attack_simulations": attacks,
                "layers_used": layers,
                "layer_results": layer_results,
                "heikal": heikal_data,
                "duration_sec": round(elapsed, 2),
            }
        )

        # Update MongoDB
        update_fields = {
            "status": "completed",
            "progress": 100,
            "current_layer": "Done",
            "total_findings": total,
            "critical_count": sev_counts["CRITICAL"],
            "high_count": sev_counts["HIGH"],
            "medium_count": sev_counts["MEDIUM"],
            "low_count": sev_counts["LOW"],
            "security_score": score,
            "result_json": result_json,
            "total_attacks": len(attacks),
            "profitable_attacks": sum(1 for a in attacks if a.get("is_profitable")),
            "max_profit_usd": max(
                (a.get("net_profit_usd", 0) for a in attacks), default=0
            ),
            "completed_at": datetime.datetime.utcnow(),
            "duration_sec": round(elapsed, 2),
        }

        # Heikal scores
        if heikal_data:
            # Aggregate Heikal scores from per-function results
            funcs = heikal_data.get("functions", {})
            if funcs:
                tunnels = [
                    f.get("tunneling", {}).get("confidence", 0) for f in funcs.values()
                ]
                waves = [
                    f.get("wave", {}).get("heuristic_score", 0) for f in funcs.values()
                ]
                holos = [
                    f.get("holographic", {}).get("similarity", 0)
                    for f in funcs.values()
                ]
                resos = [
                    f.get("resonance", {}).get("optimal_amount_eth", 0)
                    for f in funcs.values()
                ]
                update_fields["heikal_tunnel"] = (
                    sum(tunnels) / len(tunnels) if tunnels else 0
                )
                update_fields["heikal_wave"] = sum(waves) / len(waves) if waves else 0
                update_fields["heikal_holo"] = sum(holos) / len(holos) if holos else 0
                update_fields["heikal_resonance"] = (
                    sum(resos) / len(resos) if resos else 0
                )

        update_scan(scan_id, **update_fields)
        _logger.info(f"Layer scan {scan_id} complete: {total} findings, {elapsed:.1f}s")

    except Exception as e:
        _logger.error(f"Layer scan {scan_id} failed: {e}\n{traceback.format_exc()}")
        update_scan(
            scan_id,
            status="failed",
            error_message=str(e),
            progress=100,
            current_layer="Error",
            completed_at=datetime.datetime.utcnow(),
            duration_sec=round(time.time() - t0, 2),
        )


# ═══════════════════════════════════════════════════════════
#  GET /layer/scan/{scan_id} — Get layer scan results
# ═══════════════════════════════════════════════════════════


@router.get("/scan/{scan_id}")
def get_layer_scan(scan_id: str, user=Depends(get_current_user)):
    """Get the status/results of a layer scan from MongoDB."""
    user_id = user.id if hasattr(user, "id") else str(user)
    scan = get_scan(scan_id, user_id)
    if not scan:
        raise HTTPException(404, "Scan not found")

    data = scan.to_dict()
    # Flatten result_json into top-level for backward compat
    if data.get("result_json"):
        data["result"] = data["result_json"]
    return data
