from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional
import json
import os
import glob
import time
# optional meta ensembler
try:
    from Core_Engines.Meta_Ensembler import MetaEnsembler, CandidateSignal
except Exception:
    MetaEnsembler = None
    CandidateSignal = None

@dataclass
class CandidateFit:
    candidate: str           # Ø§Ø³Ù… Ø§Ù„Ø¹Ø§Ø¦Ù„Ø©: "exp1", "poly2", "k*x", "k*x + b", ...
    rmse: float
    confidence: float
    params: Dict[str, float] # Ù…Ø«Ù„ {"a": ..., "b": ...}
    n: int

class EnsembleSelector:
    """
    ÙŠØ®ØªØ§Ø± Ø£ÙØ¶Ù„ Ù†Ù…ÙˆØ°Ø¬ Ù…Ù† Ø¹Ø¯Ø© Ù…Ø±Ø´Ø­ÙŠÙ† (ÙˆØ£Ø­ÙŠØ§Ù†Ù‹Ø§ ÙŠÙ…Ø²Ø¬ Ø¨ÙŠÙ† Ù…Ø±Ø´Ø­ÙŠÙ† Ù…ØªÙ‚Ø§Ø±Ø¨ÙŠÙ†).
    Ù‚ÙˆØ§Ø¹Ø¯ Ø¨Ø³ÙŠØ·Ø©/Ù‚Ø§Ø¨Ù„Ø© Ù„Ù„ØªÙˆØ³Ø¹:
      - Ø§Ù„ÙÙˆØ² Ù„Ù…Ù† ÙŠØ­Ù‚Ù‚ Ø£Ù‚Ù„ RMSE (ÙˆØ±Ø¬Ù‘Ø­ Ø¨Ø§Ù„Ø«Ù‚Ø© Ø¹Ù†Ø¯ Ø§Ù„ØªØ¹Ø§Ø¯Ù„).
      - Ø¥Ø°Ø§ ÙƒØ§Ù† Ø§Ù„ÙØ§Ø±Ù‚ Ø§Ù„Ù†Ø³Ø¨ÙŠ ÙÙŠ RMSE â‰¤ 5% Ùˆ"Ø§Ù„Ø¹Ø§Ø¦Ù„Ø©" Ù…ØªØ·Ø§Ø¨Ù‚Ø©ØŒ Ù†Ù…Ø²Ø¬ Ø§Ù„Ù…Ø¹Ø§Ù…Ù„Ø§Øª Ø¨Ù…ØªÙˆØ³Ø· Ù…Ø±Ø¬Ù‘Ø­ Ø¨Ø§Ù„Ø«Ù‚Ø©.
    """

    CLOSE_RMSE_REL = 0.05  # 5%

    def select(self, fits: List[CandidateFit]) -> Dict[str, Any]:
        if not fits:
            return {"success": False, "error": "no candidates"}

        # Ø±ØªÙ‘Ø¨ Ø­Ø³Ø¨ (rmse ØªØµØ§Ø¹Ø¯ÙŠÙ‹Ø§ØŒ Ø«Ù… -confidence Ù†Ø²ÙˆÙ„ÙŠÙ‹Ø§)
        sorted_fits = sorted(fits, key=lambda c: (c.rmse, -c.confidence))
        top = sorted_fits[0]

        # Ù‡Ù„ Ù‡Ù†Ø§Ùƒ Ù…Ø²Ø¬ØŸ
        blended: Optional[Dict[str, Any]] = None
        for other in sorted_fits[1:]:
            if other.candidate != top.candidate:
                continue
            if self._close(top.rmse, other.rmse):
                blended = self._blend_same_family(top, other)
                break

        winner = {
            "winner": top.candidate if not blended else f"{top.candidate} (blended)",
            "rmse": blended["rmse"] if blended else top.rmse,
            "confidence": max(top.confidence, other.confidence) if blended else top.confidence, # type: ignore
            "params": blended["params"] if blended else top.params,
            "n": top.n,
            "blended": bool(blended),
        }
        return {"success": True, "result": winner}

    def _close(self, a: float, b: float) -> bool:
        if a == 0 and b == 0:
            return True
        base = max(abs(a), 1e-12)
        return abs(a - b) / base <= self.CLOSE_RMSE_REL

    def _blend_same_family(self, a: CandidateFit, b: CandidateFit) -> Dict[str, Any]:
        # Ù…Ø²Ø¬ Ø¨Ù…ØªÙˆØ³Ø· Ù…Ø±Ø¬Ù‘Ø­ Ø¨Ø§Ù„Ø«Ù‚Ø©
        wa, wb = max(a.confidence, 1e-9), max(b.confidence, 1e-9)
        params_keys = set(a.params.keys()) & set(b.params.keys())
        blended_params = {}
        for k in params_keys:
            blended_params[k] = (a.params[k] * wa + b.params[k] * wb) / (wa + wb)
        # RMSE Ø§Ù„Ù…Ù…Ø²ÙˆØ¬ (ØªØ¨Ø³ÙŠØ·): Ù…ØªÙˆØ³Ø· Ù…Ø±Ø¬Ù‘Ø­
        rmse = (a.rmse * wa + b.rmse * wb) / (wa + wb)
        return {"params": blended_params, "rmse": rmse}

# Ø£Ø¯ÙˆØ§Øª Ù…Ø³Ø§Ø¹Ø¯Ø© Ù„Ù„Ù‚Ø±Ø§Ø¡Ø©/Ø§Ù„ÙƒØªØ§Ø¨Ø© Ø¨ØµÙŠØºØ© artifacts
def _load_results_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        from agl.engines.learning_system.io_utils import read_json
        return read_json(path)

def _to_fit_items(model_json: Dict[str, Any]) -> List[CandidateFit]:
    out = []
    for item in model_json.get("results", []):
        cand = item.get("candidate", "")
        fit = item.get("fit", {})
        out.append(CandidateFit(
            candidate=cand,
            rmse=float(fit.get("rmse", 1e9)),
            confidence=float(fit.get("confidence", 0.0)),
            params={k: float(v) for k, v in fit.items() if isinstance(v, (int, float)) and k not in ("rmse", "n", "confidence")},
            n=int(fit.get("n", 0))
        ))
    return out

def run_ensemble_over_folder(
    src_dir: str = "artifacts/models",
    src_suffix: str = "_D/results.json",
    dst_suffix: str = "_E/results.json"
) -> List[Tuple[str, str]]:
    """
    ÙŠØ¨Ø­Ø« Ø¹Ù† ÙƒØ§ÙØ© Ù…Ù„ÙØ§Øª *_D/results.json ÙˆÙŠÙƒØªØ¨ *_E/results.json Ø¨Ø§Ù„Ø§Ø®ØªÙŠØ§Ø±/Ø§Ù„Ù…Ø²Ø¬.
    ÙŠØ¹ÙŠØ¯ Ù‚Ø§Ø¦Ù…Ø© (Ù…ØµØ¯Ø±, ÙˆØ¬Ù‡Ø©) Ø§Ù„ØªÙŠ ØªÙ…Øª Ù…Ø¹Ø§Ù„Ø¬ØªÙ‡Ø§.
    """
    selector = EnsembleSelector()
    processed = []
    pattern = os.path.join(src_dir, f"*{src_suffix}")
    for src in glob.glob(pattern):
        data = _load_results_json(src)
        fits = _to_fit_items(data)
        sel = selector.select(fits)
        # If there are multiple close fits from same family, try meta-ensembling
        # Prepare close models outputs: find top few with candidate == winner and rmse within 5%
        try:
            winner = sel.get('result', {}).get('winner')
            # strip blended suffix if present
            if isinstance(winner, str) and winner.endswith(' (blended)'):
                winner = winner.replace(' (blended)', '')
            close = [f for f in fits if f.candidate == winner and selector._close(f.rmse, sel['result']['rmse'])]
            if MetaEnsembler and CandidateSignal and len(close) >= 2:
                # build candidate outputs for meta ensembler from original model artifacts if available
                close_outputs = []
                for f in close:
                    # attempt to find model's predicted y (if saved in artifact) â€” fallback to params-based quick predict
                    # we look for a results.json sibling in same src folder
                    model_y = None
                    # attempt to build y_pred of length 1 from params using simple linear for now
                    try:
                        params = f.params
                        # simple synthetic prediction: use a*1 + b as single-point prediction
                        a = params.get('a', 0.0); b = params.get('b', 0.0)
                        import numpy as _np
                        model_y = _np.array([a * 1.0 + b])
                    except Exception:
                        model_y = None
                    close_outputs.append({
                        'name': f.candidate,
                        'y_pred': model_y if model_y is not None else [0.0],
                        'rmse': f.rmse,
                        'confidence': f.confidence,
                        'sigma': None,
                    })
                # apply meta blending
                try:
                    from_core = None
                    # convert to CandidateSignal list
                    cands = []
                    for m in close_outputs:
                        cands.append(CandidateSignal(name=m['name'], y_pred=m['y_pred'], rmse=m.get('rmse'), confidence=m.get('confidence'), sigma=m.get('sigma')))
                    ens_out = MetaEnsembler().blend(cands)
                    # if blending succeeded, annotate sel result with ensembled indicator
                    if ens_out and 'y' in ens_out:
                        sel['result']['meta_ensembled'] = True
                        sel['result']['meta_y'] = ens_out['y'].tolist() if hasattr(ens_out['y'], 'tolist') else ens_out['y']
                except Exception:
                    pass
        except Exception:
            pass
        base = data.get("base", "")
        out = {
            "base": base,
            "ensemble": sel,
            "yname": data.get("yname"),
            "xname": data.get("xname"),
            "ts": int(time.time())
        }
        dst = src.replace(src_suffix, dst_suffix)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        processed.append((src, dst))
    return processed

