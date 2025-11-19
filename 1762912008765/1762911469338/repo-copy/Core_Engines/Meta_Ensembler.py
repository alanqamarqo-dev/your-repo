from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np


@dataclass
class CandidateSignal:
    name: str
    y_pred: np.ndarray           # التنبؤات على شكل (N,)
    rmse: Optional[float] = None # إن وُجد
    confidence: Optional[float] = None  # 0..1 إن وُجد
    sigma: Optional[np.ndarray] = None  # عدم اليقين لكل نقطة (N,) أو ثابت


class MetaEnsembler:
    """
    تجميع تنبؤات متعددة بأوزان ذكية:
    - إذا وُجدت sigma (عدم يقين): نستخدم أوزان 1 / (sigma^2) لكل نقطة (EWMA per-sample).
    - إذا لم توجد sigma لكن توجد ثقة: نطبّع الثقة ونستخدمها كوزن ثابت لكل نموذج.
    - إذا لم يوجد كلاهما: متوسط بسيط.
    آمن ضد حالات N/A ويعمل fallback تلقائيًا.
    """
    def __init__(self, min_conf: float = 1e-6, eps: float = 1e-12):
        self.min_conf = min_conf
        self.eps = eps

    def _normalize(self, w: np.ndarray) -> np.ndarray:
        s = np.sum(w)
        return (w / (s + self.eps)) if s > 0 else np.full_like(w, 1.0 / len(w))

    def blend(self, candidates: List[CandidateSignal]) -> Dict[str, np.ndarray]:
        if not candidates:
            raise ValueError("No candidates provided to MetaEnsembler")

        # تأكد أن جميع التنبؤات نفس الطول
        lens = {len(c.y_pred) for c in candidates}
        if len(lens) != 1:
            raise ValueError(f"Inconsistent prediction lengths: {lens}")
        n = lens.pop()

        # 1) أوزان per-sample إذا توفرت سيغما
        have_sigma = any(c.sigma is not None for c in candidates)
        if have_sigma:
            # اي سيغما ناقصة تتحوّل لقيمة كبيرة (وزن صغير)
            sigmas = []
            y_stack = []
            for c in candidates:
                y_stack.append(np.asarray(c.y_pred).reshape(1, n))
                if c.sigma is None:
                    sigmas.append(np.full((1, n), 1e6))
                else:
                    s = c.sigma
                    s = np.asarray(s)
                    if s.ndim == 0:
                        s = np.full((n,), float(s))
                    sigmas.append(s.reshape(1, n))
            Y = np.vstack(y_stack)             # (K, N)
            S = np.vstack(sigmas)              # (K, N)
            W = 1.0 / (np.square(S) + self.eps)  # (K, N)
            Wn = W / (np.sum(W, axis=0, keepdims=True) + self.eps)
            y_blend = np.sum(Wn * Y, axis=0)
            return {"y": y_blend}

        # 2) لا توجد سيغما → استخدم الثقة (ثابت لكل نموذج)
        confs = []
        have_conf = any(c.confidence is not None for c in candidates)
        if have_conf:
            for c in candidates:
                conf = float(c.confidence) if c.confidence is not None else self.min_conf
                confs.append(max(conf, self.min_conf))
            w = np.asarray(confs, dtype=float)
            w = w / (np.sum(w) + self.eps)
            Y = np.vstack([np.asarray(c.y_pred).reshape(1, n) for c in candidates])  # (K, N)
            y_blend = np.sum((w.reshape(-1, 1) * Y), axis=0)
            return {"y": y_blend}

        # 3) لا سيغما ولا ثقة → متوسط بسيط
        Y = np.vstack([np.asarray(c.y_pred).reshape(1, n) for c in candidates])  # (K, N)
        y_blend = np.mean(Y, axis=0)
        return {"y": y_blend}

__all__ = ['MetaEnsembler', 'CandidateSignal']


def create_engine(config: dict | None = None):
    """Return a small engine wrapper exposing process_task for compatibility."""
    class _Engine:
        def __init__(self):
            self.name = 'Meta_Ensembler'
            self._impl = MetaEnsembler()

        def process_task(self, payload: dict) -> dict:
            try:
                # payload expects {'candidates': [ {'name', 'y_pred', ...}, ... ] }
                raw = payload.get('candidates', [])
                candidates = []
                import numpy as _np
                for c in raw:
                    y = _np.asarray(c.get('y_pred', []))
                    cand = CandidateSignal(name=c.get('name',''), y_pred=y, rmse=c.get('rmse'), confidence=c.get('confidence'), sigma=c.get('sigma'))
                    candidates.append(cand)
                out = self._impl.blend(candidates)
                # return numpy arrays as lists for JSON-serializable tests
                return {'ok': True, 'engine': self.name, 'result': {'y': out.get('y').tolist() if out.get('y') is not None else None}} # type: ignore
            except Exception as e:
                return {'ok': False, 'error': str(e)}

    return _Engine()
