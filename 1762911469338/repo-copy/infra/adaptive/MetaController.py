from __future__ import annotations
import json
from pathlib import Path
import os
from typing import Dict, Any

CFG = Path("artifacts/agl4_config.json")
CFG.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_CFG: Dict[str, Any] = {
    "harvest": {"per_domain_target": 80, "max_domains": 6},
    "reasoning": {"max_hypotheses": 40, "accept_threshold": 0.50},
    "theory": {"min_conf_for_memory": 0.60, "min_coherence_for_memory": 0.60},
    "tuning": {"step_small": 5, "step_medium": 10}
}


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write_json(path: Path, obj: Dict[str, Any]):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config() -> Dict[str, Any]:
    cfg = DEFAULT_CFG.copy()
    cfg.update(_read_json(CFG))
    return cfg


def tune_after_cycle() -> Dict[str, Any]:
    """يضبط المعاملات بناء على ملفات نواتج الدورة الأخيرة."""
    cfg = load_config()

    prog = _read_json(Path("artifacts/harvest_progress.json"))
    theory = _read_json(Path("artifacts/theory_bundle.json"))
    reason = _read_json(Path("artifacts/reasoning_eval.json"))

    coherence = float(theory.get("metrics", {}).get("coherence", theory.get("coherence", 0.0)))
    coverage = float(theory.get("metrics", {}).get("coverage", theory.get("coverage", 0.0)))
    hyp_acc = float(reason.get("hypotheses_accepted", 0))
    hyp_gen = float(reason.get("hypotheses_generated", 1))
    acc_rate = hyp_acc / max(hyp_gen, 1)

    # tuning steps
    step_s, step_m = cfg["tuning"]["step_small"], cfg["tuning"]["step_medium"]

    # 1) Coverage: increase harvest target conservatively, cap at a sensible upper bound
    if coverage < 0.40:
        new_target = cfg["harvest"].get("per_domain_target", 80) + step_m
        cfg["harvest"]["per_domain_target"] = min(new_target, cfg["harvest"].get("max_cap", 500))

    # 2) Reasoning adjustments: be conservative when reducing search space
    if coherence < 0.50:
        cfg["reasoning"]["max_hypotheses"] = max(20, cfg["reasoning"]["max_hypotheses"] - step_s)
        cfg["reasoning"]["accept_threshold"] = min(0.80, cfg["reasoning"]["accept_threshold"] + 0.05)

    if acc_rate < 0.40:
        cfg["reasoning"]["max_hypotheses"] = max(20, cfg["reasoning"]["max_hypotheses"] - step_s)

    # 3) Hysteresis for memory threshold: only raise min_conf_for_memory after N consecutive improvements
    try:
        hist_path = Path("artifacts/history/evolution.jsonl")
        N = 3
        if hist_path.exists():
            lines = hist_path.read_text(encoding="utf-8").splitlines()
            # parse last N+1 metrics to check trend
            last = []
            for ln in reversed(lines[-(N+5):]):
                try:
                    row = json.loads(ln)
                    v = row.get('metrics', {}).get('coherence')
                    if v is not None:
                        last.append(float(v))
                except Exception:
                    continue
            # check if last N entries show non-decreasing or improved average
            if len(last) >= N:
                recent = last[:N]
                # require that mean(recent) > mean(previous window) by a small margin
                prev = last[N: N*2]
                if prev:
                    if (sum(recent)/len(recent)) > (sum(prev)/len(prev)) + 0.005 and coherence >= 0.65:
                        cfg["theory"]["min_conf_for_memory"] = min(0.90, cfg["theory"]["min_conf_for_memory"] + 0.02)
                else:
                    # no previous window; be conservative
                    if coherence >= 0.75:
                        cfg["theory"]["min_conf_for_memory"] = min(0.90, cfg["theory"]["min_conf_for_memory"] + 0.01)
    except Exception:
        # best-effort: do not block tuning on analytics errors
        pass
    # Honor explicit environment overrides so an operator can prevent the
    # auto-tuner from raising the memory confidence/coherence above a chosen
    # ceiling. The env vars act as an upper cap for the tuner's increases.
    try:
        env_min_conf = os.getenv("AGL_THEORY_MIN_CONF")
        if env_min_conf is not None:
            env_val = float(env_min_conf)
            # if the tuner tried to raise the threshold above the env cap,
            # clamp it down to the env value
            if cfg.get("theory", {}).get("min_conf_for_memory") is not None:
                cfg["theory"]["min_conf_for_memory"] = min(cfg["theory"]["min_conf_for_memory"], env_val)
    except Exception:
        pass

    try:
        env_min_coh = os.getenv("AGL_THEORY_MIN_COH")
        if env_min_coh is not None:
            env_val = float(env_min_coh)
            if cfg.get("theory", {}).get("min_coherence_for_memory") is not None:
                cfg["theory"]["min_coherence_for_memory"] = min(cfg["theory"]["min_coherence_for_memory"], env_val)
    except Exception:
        pass

    _write_json(CFG, cfg)
    return cfg
