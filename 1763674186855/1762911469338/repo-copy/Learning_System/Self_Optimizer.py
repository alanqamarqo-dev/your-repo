# Learning_System/Self_Optimizer.py
import json, os, glob, math, datetime
from typing import Dict, Any, List

def _read_json(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _write_json(path: str, obj: Any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def _ema(prev: float, new: float, alpha: float=0.3) -> float:
    if prev is None:
        return new
    return alpha*new + (1-alpha)*prev

def gather_model_signals(models_root="artifacts/models") -> Dict[str, Dict[str, float]]:
    """يقرأ أحدث results.json لكل نموذج ويستخلص (winner, rmse, confidence)."""
    signals = {}
    for path in glob.glob(os.path.join(models_root, "**", "results.json"), recursive=True):
        j = _read_json(path)
        if not j:
            continue
        # شكلان محتملان: إما results[] أو ensemble.result
        if "ensemble" in j and j["ensemble"].get("success"):
            r = j["ensemble"]["result"]
            base = j.get("base", "unknown")
            signals[base] = {
                "rmse": float(r.get("rmse", math.inf)),
                "confidence": float(r.get("confidence", 0.0))
            }
        elif "results" in j and isinstance(j["results"], list) and j["results"]:
            best = sorted(j["results"], key=lambda x: x.get("fit", {}).get("rmse", math.inf))[0]
            base = j.get("base", "unknown")
            signals[base] = {
                "rmse": float(best.get("fit", {}).get("rmse", math.inf)),
                "confidence": float(best.get("fit", {}).get("confidence", 0.0))
            }
    return signals

def gather_run_signal(last_run="reports/last_run.json") -> Dict[str, float]:
    """يقرأ confidence الإجمالي من آخر تشغيل (phase_2 أو غيره)."""
    j = _read_json(last_run)
    if not j:
        return {}
    return {"run_confidence": float(j.get("confidence_score", j.get("solution", {}).get("confidence", 0.0)))}

def update_learned_patterns(kb_path="Knowledge_Base/Learned_Patterns.json",
                            model_signals:Dict[str,Dict[str,float]] = None, # type: ignore
                            alpha:float=0.3) -> Dict[str, Any]:
    kb = _read_json(kb_path) or {"version":"G.1","updated_at":None,"patterns":[]}
    changed = False
    for p in kb.get("patterns", []):
        base = p.get("base")
        sig = (model_signals or {}).get(base)
        if not sig:
            continue
        # قاعدة بسيطة: ثقة النمط ~ 1/(1+rmse) وتمزج مع أي confidence موجود بالنمط
        rmse = sig.get("rmse", None)
        conf_model = sig.get("confidence", 0.0)
        conf_from_rmse = 1.0/(1.0 + (rmse if rmse is not None else 1.0))
        new_conf = 0.5*conf_model + 0.5*conf_from_rmse

        # خزّن داخل p["fit"]["confidence"] باستخدام EMA
        if "fit" not in p: p["fit"] = {}
        prev = p["fit"].get("confidence")
        p["fit"]["confidence"] = _ema(prev, new_conf, alpha=alpha)
        changed = True
    if changed:
        kb["version"] = (kb.get("version") or "G.1").split(".")[0] + "." + datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S")
        kb["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        _write_json(kb_path, kb)
    return kb

def update_fusion_weights(cfg_path="config/fusion_weights.json",
                          signals:Dict[str,Dict[str,float]] = None, # type: ignore
                          run_conf:float = None, # type: ignore
                          step:float = 0.05,
                          floor:float = 0.4,
                          ceil:float = 1.5) -> Dict[str, float]:
    """
    يضبط أوزان الدمج (quantum_processor, code_generator, protocol_designer, mathematical_brain ...)
    بناءً على جودة النماذج وتشغيل النظام.
    سياسة بسيطة:
      - إذا run_conf >= 0.7 → زد وزن المحركات التي لديها إشارات نماذج جيدة (rmse منخفض/ثقة أعلى) بمقدار step.
      - إذا run_conf < 0.5 → خفّض وزنها بمقدار step/2.
    """
    w = _read_json(cfg_path) or {}
    if not w:
        # أوزان افتراضية معقولة
        w = {"mathematical_brain":1.0, "quantum_processor":0.6, "code_generator":1.2, "protocol_designer":0.6}
    run_conf = run_conf if run_conf is not None else 0.6

    good = []
    for base, s in (signals or {}).items():
        if s.get("rmse", math.inf) < 0.1 or s.get("confidence", 0.0) > 0.8:
            good.append(base)

    delta_up = step if run_conf >= 0.7 else (step/2 if run_conf >= 0.6 else 0.0)
    delta_dn = (step/2) if run_conf < 0.5 else 0.0

    # خرائط تقريبية من قواعد إلى محركات (يمكن تخصيصها لاحقًا)
    map_base_to_engine = {
        "ohm":"mathematical_brain",
        "hooke":"mathematical_brain",
        "projectile":"mathematical_brain",
        "rc_step":"mathematical_brain",
        "poly2":"code_generator",
        "poly2_iv":"code_generator",
        "exp1":"protocol_designer",
        "power":"quantum_processor",
    }

    for base in map_base_to_engine:
        eng = map_base_to_engine[base]
        old = w.get(eng, 1.0)
        if base in good:
            new = min(ceil, old + delta_up)
        elif delta_dn > 0:
            new = max(floor, old - delta_dn)
        else:
            new = old
        w[eng] = round(new, 3)

    _write_json(cfg_path, w)
    return w

def run_self_optimization(out_dir="reports/self_optimization",
                          models_root="artifacts/models",
                          kb_path="Knowledge_Base/Learned_Patterns.json",
                          fusion_cfg="config/fusion_weights.json") -> Dict[str, Any]:
    os.makedirs(out_dir, exist_ok=True)
    model_signals = gather_model_signals(models_root=models_root)
    run_signal = gather_run_signal()
    kb = update_learned_patterns(kb_path=kb_path, model_signals=model_signals, alpha=0.35)
    weights = update_fusion_weights(cfg_path=fusion_cfg, signals=model_signals, run_conf=run_signal.get("run_confidence", 0.6))

    report = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model_signals": model_signals,
        "run_signal": run_signal,
        "fusion_weights": weights,
        "kb_version": kb.get("version"),
        "kb_count": len(kb.get("patterns", [])),
        "status": "ok"
    }
    _write_json(os.path.join(out_dir, "self_optimization.json"), report)

    # HTML خفيف
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Self Optimization</title></head>
<body style="font-family:ui-sans-serif,system-ui">
<h2>AGL Self-Optimization</h2>
<p><b>Time:</b> {report['ts']}</p>
<p><b>KB:</b> {report['kb_version']} (patterns={report['kb_count']})</p>
<h3>Fusion Weights</h3>
<pre>{json.dumps(weights, ensure_ascii=False, indent=2)}</pre>
<h3>Model Signals</h3>
<pre>{json.dumps(model_signals, ensure_ascii=False, indent=2)}</pre>
<h3>Run Signal</h3>
<pre>{json.dumps(run_signal, ensure_ascii=False, indent=2)}</pre>
</body></html>"""
    with open(os.path.join(out_dir, "self_optimization.html"), "w", encoding="utf-8") as f:
        f.write(html)

    return report
