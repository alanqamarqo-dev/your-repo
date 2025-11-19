"""Lightweight semantic scorer used by academic/test harness.

Provides a TF-IDF based similarity if scikit-learn is available, else
falls back to difflib.SequenceMatcher. Exposes score_text_similarity() which
returns a similarity in [0.0, 1.0] and map_score_0_10() to map to 0-10.
"""
from typing import Tuple

def score_text_similarity(target: str, response: str) -> float:
    target = (target or '').strip()
    response = (response or '').strip()
    if not target or not response:
        return 0.0

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer # type: ignore
        import numpy as _np
        vec = TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5)).fit([target, response])
        m = vec.transform([target, response]).toarray() # type: ignore
        a, b = _np.array(m[0]), _np.array(m[1])
        denom = (_np.linalg.norm(a) * _np.linalg.norm(b))
        if denom <= 0:
            return 0.0
        return float(_np.dot(a, b) / denom)
    except Exception:
        # fallback to difflib
        try:
            import difflib
            seq = difflib.SequenceMatcher(None, target, response)
            ratio = seq.quick_ratio() if hasattr(seq, 'quick_ratio') else seq.ratio()
            return float(ratio)
        except Exception:
            return 0.0


def map_score_0_10(similarity: float) -> int:
    """Map a similarity in [0,1] to an integer 0..10."""
    try:
        s = max(0.0, min(1.0, float(similarity)))
        return int(round(s * 10))
    except Exception:
        return 0


if __name__ == '__main__':
    # quick smoke
    print(score_text_similarity('برهان', 'هذا نص يحتوي على برهان ممتاز'))