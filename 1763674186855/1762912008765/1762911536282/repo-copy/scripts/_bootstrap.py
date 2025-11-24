from __future__ import annotations
import sys, os
from pathlib import Path

_MARKERS = {"pyproject.toml", "setup.cfg", "requirements.txt", "Core_Engines"}


def _looks_like_project_root(p: Path) -> bool:
    # اعتبر الجذر إن وجد ملف مشروع أو مجلد Core_Engines
    return any((p / m).exists() for m in _MARKERS)


def ensure_project_root() -> Path:
    """
    يضمن إضافة جذر المشروع إلى sys.path عند تشغيل سكربتات مباشرة.
    يرجع مسار الجذر المكتشف.
    """
    here = Path(__file__).resolve()
    cur = here.parent
    last = None
    # اصعد حتى القرص الأعلى أو العثور على الجذر
    while cur != last:
        if _looks_like_project_root(cur):
            proj = str(cur)
            if proj not in sys.path:
                sys.path.insert(0, proj)
            # اضبط WORKDIR لتخزين artifacts بشكل متسق
            os.environ.setdefault("AGL_WORKDIR", str(cur / "artifacts"))
            return cur
        last, cur = cur, cur.parent
    # fallback: أضف parent مرتين كأضعف الإيمان
    up2 = here.parent.parent
    if str(up2) not in sys.path:
        sys.path.insert(0, str(up2))
    return up2
