import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import argparse, os, json, datetime, sys
from string import Template
from datetime import timezone
import importlib.util

# Load InferenceEngine directly from file to avoid executing Learning_System.__init__
ie_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Learning_System", "Inference_Engine.py"))
spec = importlib.util.spec_from_file_location("inference_engine_mod", ie_path)
if spec and spec.loader:
  inference_mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(inference_mod)  # type: ignore
  InferenceEngine = inference_mod.InferenceEngine
else:
  raise ImportError(f"cannot load Inference_Engine from {ie_path}")

TEMPLATE = Template("""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8"/>
<title>AGL Inference Report</title>
<style>
body{font-family:system-ui,Segoe UI,Arial;max-width:900px;margin:24px auto;line-height:1.7}
.card{border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:16px 0}
h1{margin:0 0 8px}
h2{margin:8px 0}
code,kbd,pre{background:#f6f8fa;border-radius:6px;padding:2px 6px}
table{border-collapse:collapse;width:100%}
td,th{border:1px solid #e5e7eb;padding:8px;text-align:right}
.badge{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:999px;padding:2px 10px;font-size:12px}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace}
.blended-badge{background:#ffefc7;color:#7a4a00;padding:2px 8px;border-radius:999px;margin-left:8px}
.meta-box{background:#f8fafc;border:1px dashed #cbd5e1;padding:8px;border-radius:8px;margin-top:12px}
</style>
</head>
<body>
<h1>تقرير الاستدلال – AGL</h1>
<div class="card">
  <div><span class="badge">النموذج</span> <strong>$base</strong></div>
  <div><span class="badge">التاريخ</span> $date</div>
</div>

<div class="card">
  <h2>المدخلات</h2>
  <table>
    <tr><th>الحقل</th><th>القيمة</th></tr>
    <tr><td>base</td><td class="mono">$base</td></tr>
    <tr><td>x</td><td class="mono">$x_disp</td></tr>
  </table>
</div>

<div class="card">
  <h2>النتيجة $blended_badge</h2>
  <pre class="mono">$result_json</pre>
  $meta_block
</div>

<div class="card">
  <h2>المشتقات (إن وُجدت)</h2>
  <pre class="mono">$derived_json</pre>
</div>

<div class="card">
  <h2>ملاحظات</h2>
  <ul>
    <li>القيم مستندة إلى النمط الفائز المحفوظ في <code>Knowledge_Base/Learned_Patterns.json</code>.</li>
    <li>لإعادة التدريب: استخدم <code>scripts/train_phaseD.py</code> أو CLI التعلم الذاتي.</li>
  </ul>
</div>
</body>
</html>
""")

def main():
    ap = argparse.ArgumentParser("AGL Inference HTML Report")
    ap.add_argument("--base", required=True, help="ohm|hooke|poly2|rc_step|power|exp1|projectile|poly2_iv...")
    ap.add_argument("--x", nargs="*", type=float, help="قيمة/قيم x (اختياري)")
    ap.add_argument("--out", default=None, help="مسار ملف HTML الناتج")
    args = ap.parse_args()

    eng = InferenceEngine()
    x = None
    if args.x:
        x = args.x[0] if len(args.x)==1 else args.x

    # run inference
    result = eng.predict(args.base, x) if x is not None else eng.predict(args.base, 0.0)

    # pick derived block if present
    derived = result.get("derived", {})

    # out path (timezone-aware)
    ts = datetime.datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join("reports")
    os.makedirs(out_dir, exist_ok=True)
    out_html = args.out or os.path.join(out_dir, f"infer_{args.base}_{ts}.html")

    # build optional meta display block: show if blending/meta_ensembled present
    blended_badge = ""
    meta_block = ""
    try:
        if isinstance(result.get('blended', False), bool) and result.get('blended'):
            blended_badge = '<span class="blended-badge">Blended</span>'
        if result.get('meta_ensembled'):
            mb = []
            meta = result.get('meta_y')
            if meta is not None:
                try:
                    import numpy as _np
                    meta_arr = _np.array(meta)
                    mb.append(f"<div><b>Meta ensembled y (first values):</b> {meta_arr.tolist()[:5]}</div>")
                except Exception:
                    mb.append(f"<div><b>Meta ensembled y:</b> {str(meta)}</div>")
            # include confidence/sigma if present in the result
            if 'confidence' in result:
                mb.append(f"<div><b>Ensemble confidence:</b> {result.get('confidence')}</div>")
            if 'sigma' in result:
                mb.append(f"<div><b>Sigma:</b> {result.get('sigma')}</div>")
            meta_block = '<div class="meta-box">' + '\n'.join(mb) + '</div>'
    except Exception:
        meta_block = ""

    # render (use timezone-aware ISO timestamp)
    html = TEMPLATE.substitute(
        base=args.base,
        date=datetime.datetime.now(timezone.utc).isoformat(),
        x_disp=json.dumps(x, ensure_ascii=False),
        result_json=json.dumps(result, ensure_ascii=False, indent=2),
        derived_json=json.dumps(derived, ensure_ascii=False, indent=2),
        blended_badge=blended_badge,
        meta_block=meta_block,
    )

    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"wrote {out_html}")

if __name__ == "__main__":
    main()
