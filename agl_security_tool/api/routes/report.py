"""
AGL Security — Report Routes
مسارات التقارير — تصدير Markdown / JSON

GET /api/v1/report/{id}         → Full report
GET /api/v1/report/{id}/json    → JSON export
GET /api/v1/report/{id}/md      → Markdown export
"""

import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session

from ..database import get_db, Scan, User
from ..auth import get_current_user

router = APIRouter(prefix="/api/v1/report", tags=["Report"])


@router.get("/{scan_id}")
def get_report(
    scan_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """تقرير كامل — Full report as JSON."""
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user.id).first()
    if not scan:
        raise HTTPException(404, "فحص غير موجود — Scan not found")
    if scan.status != "completed":
        raise HTTPException(400, "الفحص لم يكتمل بعد — Scan not completed yet")

    return {
        "scan_id": scan.id,
        "target": scan.target_name,
        "mode": scan.scan_mode,
        "score": scan.security_score,
        "summary": {
            "critical": scan.critical_count,
            "high": scan.high_count,
            "medium": scan.medium_count,
            "low": scan.low_count,
            "total": scan.total_findings,
        },
        "heikal": {
            "xi": scan.heikal_xi,
            "wave": scan.heikal_wave,
            "tunnel": scan.heikal_tunnel,
            "holo": scan.heikal_holo,
            "resonance": scan.heikal_resonance,
        },
        "attacks": {
            "total": scan.total_attacks,
            "profitable": scan.profitable_attacks,
            "max_profit_usd": scan.max_profit_usd,
        },
        "duration_sec": scan.duration_sec,
        "created_at": scan.created_at.isoformat() if scan.created_at else "",
        "result": scan.result_json,
    }


@router.get("/{scan_id}/json")
def export_json(
    scan_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """تصدير JSON — Export as JSON file."""
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user.id).first()
    if not scan or scan.status != "completed":
        raise HTTPException(404, "فحص غير مكتمل — Scan not found or not completed")

    return JSONResponse(
        content=scan.result_json or {},
        headers={
            "Content-Disposition": f"attachment; filename=agl_report_{scan_id[:8]}.json"
        },
    )


@router.get("/{scan_id}/md", response_class=PlainTextResponse)
def export_markdown(
    scan_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """تصدير Markdown — Export as Markdown."""
    scan = db.query(Scan).filter(Scan.id == scan_id, Scan.user_id == user.id).first()
    if not scan or scan.status != "completed":
        raise HTTPException(404, "فحص غير مكتمل — Scan not found or not completed")

    result = scan.result_json or {}
    findings = result.get("findings", [])
    attacks = result.get("attack_simulations", [])

    lines = [
        f"# AGL Security Report — {scan.target_name}",
        f"",
        f"**Scan Mode:** {scan.scan_mode} | **Date:** {scan.created_at.strftime('%Y-%m-%d %H:%M') if scan.created_at else 'N/A'} | **Duration:** {scan.duration_sec}s",
        f"",
        f"## Summary",
        f"",
        f"| Severity | Count |",
        f"|----------|-------|",
        f"| 🔴 CRITICAL | {scan.critical_count} |",
        f"| 🟠 HIGH | {scan.high_count} |",
        f"| 🟡 MEDIUM | {scan.medium_count} |",
        f"| 🟢 LOW | {scan.low_count} |",
        f"| **Total** | **{scan.total_findings}** |",
        f"",
        f"**Security Score:** {scan.security_score}/100",
        f"",
    ]

    # Heikal Math
    if scan.heikal_xi is not None:
        lines += [
            f"## Heikal Math Analysis",
            f"",
            f"| Algorithm | Score |",
            f"|-----------|-------|",
            f"| Wave | {scan.heikal_wave or 'N/A'} |",
            f"| Tunneling | {scan.heikal_tunnel or 'N/A'} |",
            f"| Holographic | {scan.heikal_holo or 'N/A'} |",
            f"| Resonance | {scan.heikal_resonance or 'N/A'} |",
            f"| **Composite ξ** | **{scan.heikal_xi}** |",
            f"",
        ]

    # Findings
    lines += [f"## Findings", f""]
    for i, f in enumerate(findings, 1):
        sev = f.get("severity", "LOW").upper()
        icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(
            sev, "⚪"
        )
        lines += [
            f"### {i}. {icon} {sev} — {f.get('category', 'Unknown')}",
            f"",
            f"**Function:** `{f.get('function', 'N/A')}`",
            f"",
            f"**Description:** {f.get('description', 'N/A')}",
            f"",
        ]
        if f.get("proof"):
            lines += [f"**Z3 Proof:** {f['proof'].get('status', 'N/A')}", f""]
        if f.get("recommendation"):
            lines += [f"**Fix:** {f['recommendation']}", f""]
        lines.append("---")
        lines.append("")

    # Attack simulations
    if attacks:
        lines += [f"## Attack Simulations", f""]
        for i, a in enumerate(attacks, 1):
            profitable = "✅ مربح" if a.get("is_profitable") else "❌ غير مربح"
            lines += [
                f"### Attack #{i}: {a.get('attack_type', 'Unknown')}",
                f"- **Profit:** ${a.get('net_profit_usd', 0):,.2f}",
                f"- **Status:** {profitable}",
                f"",
            ]

    md_text = "\n".join(lines)
    return PlainTextResponse(
        content=md_text,
        headers={
            "Content-Disposition": f"attachment; filename=agl_report_{scan_id[:8]}.md"
        },
    )
