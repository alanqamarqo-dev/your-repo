# -*- coding: utf-8 -*-
"""
Phase G: جمع الأنماط من نتائج التدريب مع فلترة جودة وكتابة Learned_Patterns.json
Usage:
  python -m scripts.phase_g_save_patterns --models-root artifacts/models --out Knowledge_Base/Learned_Patterns.json [--ascii]
"""
import json, sys, os, glob, math, argparse
from datetime import datetime, timezone

# عتبات الجودة حسب عائلة النموذج
QUALITY = {
    "poly2":  {"rmse_max": 0.15, "conf_min": 0.0},
    "poly2_iv":{"rmse_max": 0.15, "conf_min": 0.0},
    "ohm":    {"rmse_max": 0.10, "conf_min": 0.0},
    "hooke":  {"rmse_max": None, "conf_min": 0.50},  # مع تحذير لو b كبير
    "exp1":   {"rmse_max": 0.05, "conf_min": 0.60},
    "rc_step":{"rmse_max": 0.05, "conf_min": 0.60},
    "power":  {"rmse_max": None, "conf_min": 0.60},
    "projectile":{"rmse_max": 0.02, "conf_min": 0.90},
}

def safe_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

def status_for(base, rmse, conf, params):
    thr = QUALITY.get(base, {})
    rmse_ok = True if thr.get("rmse_max") is None else (rmse is not None and rmse <= thr["rmse_max"])
    conf_ok = True if thr.get("conf_min") is None else (conf is not None and conf >= thr["conf_min"])
    status = "accepted" if (rmse_ok and conf_ok) else "draft"
    reason = []
    if not rmse_ok: reason.append("rmse_high")
    if not conf_ok: reason.append("low_confidence")
    # تحذير خاص لـ hooke: لو الاعتراض b كبير مقارنة بالمقياس
    if base == "hooke" and params and abs(safe_float(params.get("b",0),0)) > 0.2:
        reason.append("hooke_large_intercept")
        if status == "accepted":
            status = "draft"
    return status, (",".join(reason) if reason else "ok")

def schema_and_derived(base, winner, params, ascii_mode=False):
    # توليد صيغة نصية ومشتقات مفيدة
    a = safe_float(params.get("a"))
    b = safe_float(params.get("b"))
    approx = "~" if ascii_mode else "≈"
    dot = "*" if ascii_mode else "·"

    if base in ("poly2","poly2_iv"):
        schema = f"V(I) {approx} a{dot}I^2 + b"
        derived = {"dV/dI": f"dVdI(I) = 2{dot}a{dot}I" if not ascii_mode else "dVdI(I) = 2*a*I"}
    elif base in ("projectile",):
        schema = f"s(t) {approx} a{dot}t^2 + b{dot}t (+ c{approx}0)"
        derived = {"g≈" if not ascii_mode else "g~": f"g {approx} 2{dot}a"}
    elif base in ("rc_step","exp1"):
        schema = f"Vc(t) {approx} b + exp(a{dot}t)"
        tau = None
        if a is not None and a != 0:
            tau = -1.0/a
        derived = {"tau": tau} if tau is not None else {}
    elif base in ("ohm",):
        schema = f"V(I) {approx} a{dot}I + b"  # عند استخدام نموذج خطي
        derived = {
            "R≈" if not ascii_mode else "R~": "a",
            "P(I)": f"I{dot}(a{dot}I + b)" if not ascii_mode else "I*(a*I + b)"
        }
    elif base in ("power",):
        schema = "y ~ c*x^n" if ascii_mode else "y ≈ c·x^n"
        derived = {}
    else:
        schema = f"{winner}(x)"  # افتراضي
        derived = {}
    return schema, derived

def load_results(paths):
    items = []
    for p in paths:
        try:
            from Learning_System.io_utils import read_json
            J = read_json(p)
            base = J.get("base")
            # شكلان محتملان: ensemble.result أو results[0]
            ens = J.get("ensemble", {})
            if ens and ens.get("success") and "result" in ens:
                winner = ens["result"].get("winner")
                fit = {
                    "a": ens["result"].get("params", {}).get("a"),
                    "b": ens["result"].get("params", {}).get("b"),
                    "rmse": ens["result"].get("rmse"),
                    "n": ens["result"].get("n"),
                    "confidence": ens["result"].get("confidence"),
                }
            else:
                best = (J.get("results") or [])[0] if (J.get("results")) else None
                winner = best.get("candidate") if best else None
                fitd = best.get("fit", {}) if best else {}
                fit = {
                    "a": fitd.get("a"),
                    "b": fitd.get("b"),
                    "rmse": fitd.get("rmse"),
                    "n": fitd.get("n"),
                    "confidence": fitd.get("confidence"),
                }
            if base and winner and fit:
                items.append((p, base, winner, fit))
        except Exception:
            pass
    return items
import os, json, glob, re
from datetime import datetime, timezone

def _unit(s):
    m = re.search(r"\[(.+?)\]", s)
    return (m.group(1) if m else "").strip()

def _load_results(paths):
    items=[]
    for p in paths:
        try:
            from Learning_System.io_utils import read_json
            data = read_json(p)
            # دعم تنسيقين: (results[]) أو (ensemble.result)
            if "ensemble" in data and data["ensemble"].get("success"):
                r = data["ensemble"]["result"]
                fit = r.get("params", {})
                item = {
                    "base": data.get("base"),
                    "winner": r.get("winner"),
                    "fit": {**fit, "rmse": r.get("rmse"), "n": r.get("n")},
                    "yname": data.get("yname",""),
                    "xname": data.get("xname","")
                }
                items.append(item)
            elif "results" in data and data["results"]:
                best=min(data["results"], key=lambda x: x["fit"]["rmse"])
                fit=best["fit"]
                item={
                    "base": data.get("base"),
                    "winner": best.get("candidate"),
                    "fit": fit,
                    "yname": data.get("yname",""),
                    "xname": data.get("xname","")
                }
                items.append(item)
        except Exception:
            pass
    return items

def _derive_pattern(it):
    # default units mapping
    DEFAULT_UNITS = {
        "hooke":      {"y":"N",  "x":"m"},
        "ohm":        {"y":"V",  "x":"A"},
        "poly2_iv":   {"V":"V",  "I":"A"},
        "poly2":      {"V":"V",  "I":"A"},
        "rc_step":    {"y":"V",  "x":"s", "tau":"s"},
        "projectile": {"s":"m",  "t":"s", "g":"m/s^2"},
        "power":      {"y":"",   "x":""}
    }

    def _merge_units(u_from_names, base):
        d = {}
        if u_from_names.get("y"): d["y"] = u_from_names["y"]
        if u_from_names.get("x"): d["x"] = u_from_names["x"]
        d.update(DEFAULT_UNITS.get(base, {}))
        return d

    base=it["base"]; winner=it["winner"]; fit=it["fit"]
    yu=_unit(it["yname"]); xu=_unit(it["xname"])
    units_from_names={"y":yu,"x":xu}
    # normalize numeric fit values where possible
    fit_num = {k: (float(v) if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).lstrip('-').isdigit()) else v) for k,v in fit.items()}
    pattern={"base":base,"winner":winner,"fit":fit_num}

    # rc_step ~ exp1
    if base=="rc_step" and winner=="exp1" and "a" in fit and fit["a"]!=0:
        tau = -1.0/fit["a"]
        pattern.update({
            "schema":"Vc(t) ≈ b + exp(a·t)",
            "derived":{"tau":"tau = -1/a"},
            "units": _merge_units(units_from_names, base),
            "notes":"tau computed from negative a" if fit["a"]<0 else "warning: a>=0"
        })

    # poly2 (IV)
    elif base in ("poly2_iv","poly2") and winner=="poly2" and "a" in fit and "b" in fit:
        pattern.update({
            "schema":"V(I) ≈ a·I^2 + b",
            "derived":{"dV/dI":"dVdI(I) = 2·a·I"},
            "units": _merge_units(units_from_names, base),
            "notes":"differential resistance depends on current"
        })

    # projectile
    elif base=="projectile" and winner=="poly2" and "a" in fit:
        g = 2.0*fit["a"]
        u = _merge_units(units_from_names, base)
        pattern.update({
            "schema":"s(t) ≈ a·t^2 + b·t (+ c≈0)",
            "derived":{"g≈":"g ≈ 2·a"},
            "units": u,
            "notes": f"g≈{g:.3f} {u.get('g','m/s^2')}"
        })

    # hooke
    elif base=="hooke" and winner=="hooke" and "a" in fit:
        pattern.update({
            "schema":"F(x) ≈ k·x + b",
            "derived":{"E_p(x)":"E_p = 0.5·k·x^2  (if |b|≈0)"},
            "units": _merge_units(units_from_names, base),
            "notes":"k≈a; if |b| small, standard Hooke energy holds"
        })

    # ohm
    elif base=="ohm" and winner=="ohm" and "a" in fit:
        pattern.update({
            "schema":"V(I) ≈ R·I + V0",
            "derived":{"R≈":"R≈a", "P(I)":"P=V·I=I·(a·I + b)"},
            "units": _merge_units(units_from_names, base),
            "notes":"linear IV; a is slope (R)"
        })

    # generic power law y ≈ A·x^B
    elif base=="power" and winner=="power" and "a" in fit and "b" in fit:
        pattern.update({
            "schema":"y ≈ A·x^B",
            "derived":{"dy/dx":"dy/dx = A·B·x^(B-1)"},
            "units": _merge_units(units_from_names, base),
            "notes":"power-law fit"
        })

    # generic exp1 (if base itself labeled exp1)
    elif base=="exp1" and winner=="exp1" and "a" in fit:
        pattern.update({
            "schema":"y ≈ b + exp(a·x)",
            "derived":{"tau":"tau = -1/a (if a<0)"},
            "units": _merge_units(units_from_names, base),
            "notes":"generic exponential"
        })

    else:
        # fallback: at least write merged units
        pattern["units"] = _merge_units(units_from_names, base)

    return pattern

def main(models_root="artifacts/models", out="Knowledge_Base/Learned_Patterns.json"):
    paths=glob.glob(os.path.join(models_root,"**","results.json"), recursive=True)
    items=_load_results(paths)
    patterns=[]
    for it in items:
        p=_derive_pattern(it)
        if p: patterns.append(p)

    doc={
        "version":"G.1",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "patterns": patterns
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,"w",encoding="utf-8") as f: json.dump(doc,f,ensure_ascii=False,indent=2)

    # تقرير مختصر
    print("Saved patterns:", len(patterns))
    for p in patterns:
        print(f"- {p['base']} -> {p.get('schema','?')} (winner={p['winner']})")

if __name__=="__main__":
    main()
