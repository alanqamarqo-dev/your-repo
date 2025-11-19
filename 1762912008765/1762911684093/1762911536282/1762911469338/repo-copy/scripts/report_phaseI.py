#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase I: Interpretive Visual Report
يجمع أفضل النماذج (ensemble winners) + العلاقات المشتقة من التعميم
ويُخرج تقرير HTML رسومي واحد.

تشغيل:
  python -m scripts.report_phaseI \
    --models-dir artifacts/models \
    --gen-dir artifacts/generalization \
    --out reports/interpretive_report.html
"""
from __future__ import annotations
import os, json, base64, io, argparse, glob, math, textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

# matplotlib للرسومات (بدون أنماط خاصة)
import matplotlib
matplotlib.use("Agg")  # للرسم بدون واجهة
import matplotlib.pyplot as plt

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def safe_read_json(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def b64_png(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")

def human(num: float) -> str:
    if num is None:
        return "-"
    try:
        numf = float(num)
    except Exception:
        return str(num)
    if abs(numf) >= 1000 or (abs(numf) < 1 and numf != 0):
        return f"{numf:.6g}"
    return f"{numf:.4f}"

def pick_ensemble_winner(model_json: dict) -> Optional[dict]:
    if not model_json:
        return None
    if "ensemble" in model_json and model_json["ensemble"] and model_json["ensemble"].get("success"):
        return model_json["ensemble"]["result"]
    results = model_json.get("results") or []
    if results:
        r0 = results[0]
        fit = r0.get("fit", {})
        return {
            "winner": r0.get("candidate"),
            "rmse": fit.get("rmse"),
            "confidence": fit.get("confidence"),
            "params": {k: v for k, v in fit.items() if k in ("a", "b")},
            "n": fit.get("n")
        }
    return None

def synth_curve(candidate: str, params: Dict[str, float], x_min: float, x_max: float, n: int = 200) -> Tuple[List[float], List[float]]:
    xs = [x_min + i*(x_max - x_min)/max(n-1,1) for i in range(n)]
    a = float(params.get("a", 0.0))
    b = float(params.get("b", 0.0))

    def f_exp1(x):
        return b + math.e**(a*x)

    def f_poly2(x):
        return a * (x**2) + b

    def f_ohm(x):
        return a*x + b

    def f_power(x):
        A, B = a, b
        xx = max(x, 1e-9)
        return A*(xx**B)

    if candidate in ("exp1",):
        ys = [f_exp1(x) for x in xs]
    elif candidate in ("poly2", "a*x**2"):
        ys = [f_poly2(x) for x in xs]
    elif candidate in ("ohm", "k*x", "k*x + b"):
        ys = [f_ohm(x) for x in xs]
    elif candidate in ("power",):
        ys = [f_power(x) for x in xs]
    else:
        ys = [a*x + b for x in xs]
    return xs, ys

def default_domain(candidate: str, params: Dict[str, float]) -> Tuple[float,float]:
    a = float(params.get("a", 0.0))
    if candidate == "exp1":
        if a < 0:
            tau = -1.0/a if a != 0 else 1.0
            return (0.0, max(1e-6, 5.0*tau))
        return (0.0, 10.0)
    if candidate in ("poly2","a*x**2"):
        return (0.0, 10.0)
    if candidate in ("ohm","k*x","k*x + b"):
        return (0.0, 1.0)
    if candidate == "power":
        return (1e-6, 10.0)
    return (0.0, 1.0)

def plot_model_preview(base: str, winner: str, params: Dict[str,float]) -> str:
    x0, x1 = default_domain(winner, params)
    xs, ys = synth_curve(winner, params, x0, x1, n=400)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(xs, ys, lw=2)
    ax.set_title(f"{base} → {winner}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, alpha=0.25)
    return b64_png(fig)

@dataclass
class DerivedRelation:
    name: str
    inputs: Dict[str, Any]
    derived: Dict[str, Any]

def load_generalization(gen_dir: str) -> List[DerivedRelation]:
    out: List[DerivedRelation] = []
    if not os.path.isdir(gen_dir):
        return out
    for path in glob.glob(os.path.join(gen_dir, "*.json")):
        data = safe_read_json(path)
        if not data:
            continue
        if "bundle" in data:
            for item in data["bundle"]:
                out.append(DerivedRelation(
                    name=item.get("relation") or item.get("name") or os.path.basename(path),
                    inputs=item.get("inputs", {}),
                    derived=item.get("derived", {})
                ))
        else:
            out.append(DerivedRelation(
                name=data.get("relation") or data.get("name") or os.path.basename(path),
                inputs=data.get("inputs", {}),
                derived=data.get("derived", {})
            ))
    return out

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>تقرير تفسيري بصري - Phase I</title>
<style>
  body {{ margin: 24px; {font_family} line-height: 1.6; }}
  h1, h2, h3 {{ margin: 0.2em 0; }}
  .card {{ border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; margin: 16px 0; }}
  .muted {{ color: #6b7280; font-size: 0.95em; }}
  .row {{ display: flex; gap: 16px; flex-wrap: wrap; }}
  .col {{ flex: 1 1 360px; min-width: 320px; }}
  .kv {{ background:#fafafa; padding: 12px; border-radius:8px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
  img.plot {{ max-width: 100%; height: auto; display: block; margin: 8px 0; border-radius: 8px; border:1px solid #eee; }}
</style>
</head>
<body>
  <h1>تقرير تفسيري بصري (Phase I)</h1>
  <div class="muted">وقت الإنشاء: {now} • المصدر: artifacts/models & artifacts/generalization</div>

  <div class="card">
    <h2>أفضل النماذج (Ensemble Winners)</h2>
    {models_section}
  </div>

  <div class="card">
    <h2>العلاقات المشتقة (التعميم الذكي)</h2>
    {derived_section}
  </div>

  <div class="muted">AGL • Phase I • {now}</div>
</body>
</html>
"""

def render_models_section(models: List[dict]) -> str:
    blocks = []
    for m in models:
        base = m.get("base","-")
        winner = m.get("winner","-")
        rmse = human(m.get("rmse")) # type: ignore
        conf = human(m.get("confidence")) # type: ignore
        n    = m.get("n")
        params = m.get("params", {})
        a = human(params.get("a"))
        b = human(params.get("b"))
        img_b64 = m.get("preview_b64")
        img_tag = f'<img class="plot" src="data:image/png;base64,{img_b64}" alt="plot {base}">' if img_b64 else ""
        kv = textwrap.dedent(f"""
        <div class="kv">
        base: {base}<br>
        winner: {winner}<br>
        rmse: {rmse} • confidence: {conf} • n: {n}<br>
        params: a={a}, b={b}
        </div>
        """).strip()
        blocks.append(f'<div class="row"><div class="col">{kv}</div><div class="col">{img_tag}</div></div>')
    return "\n".join(blocks) if blocks else "<div class='muted'>لا يوجد نماذج.</div>"

def render_derived_section(relations: List[DerivedRelation]) -> str:
    if not relations:
        return "<div class='muted'>لا يوجد علاقات مشتقة.</div>"
    blocks = []
    for r in relations:
        inp = json.dumps(r.inputs, ensure_ascii=False, indent=2)
        drv = json.dumps(r.derived, ensure_ascii=False, indent=2)
        blk = f"""
        <div class="card">
          <h3>{r.name}</h3>
          <div class="row">
            <div class="col"><div class="kv"><strong>المدخلات</strong><pre>{inp}</pre></div></div>
            <div class="col"><div class="kv"><strong>الناتج المشتق</strong><pre>{drv}</pre></div></div>
          </div>
        </div>
        """
        blocks.append(blk)
    return "\n".join(blocks)

def collect_models(models_dir: str) -> List[dict]:
    out = []
    if not os.path.isdir(models_dir):
        return out
    for path in glob.glob(os.path.join(models_dir, "**", "results.json"), recursive=True):
        data = safe_read_json(path)
        if not data:
            continue
        winner = pick_ensemble_winner(data)
        if not winner:
            continue
        base = data.get("base","-")
        params = winner.get("params") or {}
        prev = None
        try:
            prev = plot_model_preview(base, winner.get("winner","-"), params)
        except Exception:
            prev = None
        out.append({
            "base": base,
            "winner": winner.get("winner"),
            "rmse": winner.get("rmse"),
            "confidence": winner.get("confidence"),
            "n": winner.get("n"),
            "params": params,
            "preview_b64": prev
        })
    out.sort(key=lambda d: (float("inf") if d.get("rmse") is None else d["rmse"]))
    return out

def main():
    ap = argparse.ArgumentParser(description="Phase I Interpretive Report")
    ap.add_argument("--models-dir", default="artifacts/models")
    ap.add_argument("--gen-dir", default="artifacts/generalization")
    ap.add_argument("--out", default="reports/interpretive_report.html")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    models = collect_models(args.models_dir)
    relations = load_generalization(args.gen_dir)

    html = HTML_TEMPLATE.format(
        now=utc_now_iso(),
        models_section=render_models_section(models),
        derived_section=render_derived_section(relations),
        font_family="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans Arabic', 'Noto Naskh Arabic', Arial, sans-serif;"
    )

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"wrote {args.out}")

if __name__ == "__main__":
    main()
