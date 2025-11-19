from __future__ import annotations
import json, time, hashlib
from pathlib import Path
from typing import List, Dict, Any

MEM_PATH = Path("artifacts/memory/long_term.jsonl")
MEM_PATH.parent.mkdir(parents=True, exist_ok=True)


def _row_id(payload: Dict[str, Any]) -> str:
    h = hashlib.sha1(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return h[:16]


def save_theory_items(theory_bundle_path: str,
                      min_conf: float = 0.60,
                      min_coherence: float = 0.60) -> int:
    """يسجّل أفضل السرديات/الفرضيات من bundle في الذاكرة."""
    p = Path(theory_bundle_path)
    if not p.exists():
        return 0
    bundle = json.loads(p.read_text(encoding="utf-8"))
    written = 0
    # bundle may have metrics.coherence or top-level coherence
    coherence = float(bundle.get("metrics", {}).get("coherence", bundle.get("coherence", 0)))
    # نحفظ فقط إن كانت النسخة معقولة
    if coherence < min_coherence:
        return 0

    items: List[Dict[str, Any]] = bundle.get("narratives", [])
    # load existing ids to avoid duplicates
    existing_ids = set()
    if MEM_PATH.exists():
        try:
            for ln in MEM_PATH.read_text(encoding='utf-8').splitlines():
                try:
                    r = json.loads(ln)
                    if 'id' in r:
                        existing_ids.add(r['id'])
                except Exception:
                    continue
        except Exception:
            existing_ids = set()

    with MEM_PATH.open("a", encoding="utf-8") as f:
        for it in items:
            try:
                conf = float(it.get("confidence", 0))
            except Exception:
                conf = 0.0
            if conf >= min_conf:
                rec = {
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "kind": "theory",
                    "domain": it.get("domain"),
                    "text": it.get("hypothesis") or it.get("text"),
                    "support": it.get("support", []),
                    "confidence": conf,
                    "coherence": coherence
                }
                rec["id"] = _row_id(rec)
                if rec["id"] in existing_ids:
                    continue
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                existing_ids.add(rec["id"])
                written += 1
    return written


def suggest_harvest_hints(max_items: int = 12) -> List[str]:
    """يولّد تلميحات للحصاد القادم (keywords / subtopics) من الذاكرة."""
    if not MEM_PATH.exists():
        return []
    lines = MEM_PATH.read_text(encoding="utf-8").splitlines()[-300:]
    hints, seen = [], set()
    for ln in reversed(lines):
        try:
            row = json.loads(ln)
        except Exception:
            continue
        txt = str(row.get("text", ""))
        dom = row.get("domain", "general") or "general"
        for chunk in [w.strip(" '،.؟") for w in txt.split("مع")[:2]]:
            key = f"{dom}:{chunk}"
            if 6 <= len(chunk) <= 120 and key not in seen:
                seen.add(key)
                hints.append(f"[{dom}] {chunk}")
            if len(hints) >= max_items:
                break
        if len(hints) >= max_items:
            break
    return list(reversed(hints))


def suggest_reasoning_pairs(max_pairs: int = 20) -> List[Dict[str, str]]:
    """مرشّح علاقات/أزواج للاستدلال السببي."""
    if not MEM_PATH.exists():
        return []
    lines = MEM_PATH.read_text(encoding="utf-8").splitlines()[-400:]
    buf = []
    for ln in lines:
        try:
            buf.append(json.loads(ln))
        except Exception:
            pass
    pairs, seen = [], set()
    for i in range(len(buf) - 1):
        a, b = buf[i], buf[i + 1]
        if a.get("domain") == b.get("domain"):
            pair = {"domain": a["domain"], "a": a.get("text"), "b": b.get("text")}
            k = json.dumps(pair, ensure_ascii=False, sort_keys=True)
            if k not in seen:
                seen.add(k)
                pairs.append(pair)
        if len(pairs) >= max_pairs:
            break
    return pairs
