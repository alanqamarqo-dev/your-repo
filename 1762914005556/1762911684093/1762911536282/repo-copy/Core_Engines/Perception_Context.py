import re
import json
from typing import Dict, Any

SYMBOL_PATTERN = re.compile(r"[A-Za-z0-9_\|\u27E8\u27E9\u2318⟨⟩ψρΨΡHUtTR]+")


def extract_features(text: str) -> Dict[str, Any]:
    """Extract symbolic tokens, unit mentions, structural cues and domain signals.

    Returns a dict with keys: tokens, units, structures, reaction_arrows, domain_signals
    """
    tx = (text or "").replace('\n', ' ')
    features: Dict[str, Any] = {
        "tokens": [],
        "units": [],
        "structures": [],
        "reaction_arrows": False,
        "domain_signals": {},
    }

    # tokens: explicit symbols like ψ, ρ, H, U, |1〉, det, Tr
    symbols = re.findall(r"ψ|ρ|\|[^\s]+\u203A?|\|[^\s]+\u27E9?|det|Det|trace|Tr|eigen|λ|λ_i|H|U", tx)
    features["tokens"] = symbols

    # units: simple heuristics for presence of units
    unit_hits = re.findall(r"\b(V|volt|فولت|A|amp|أمبير|Ω|ohm|أوم|mol|J|s|Hz|F|H)\b", tx)
    features["units"] = list(set(unit_hits))

    # structures: matrix/operator/polynomial/reaction
    if re.search(r"matrix|مصفوفة|مؤثر|operator|operator|tensor|مُؤَثِّر", tx, re.I):
        features["structures"].append("matrix")
    if re.search(r"polynom|polynomial|كثير|حدود|مقارب", tx, re.I):
        features["structures"].append("polynomial")
    if re.search(r"->|→|⇌|\breact|تفاعل|موازنة", tx):
        features["structures"].append("reaction")
        features["reaction_arrows"] = True

    # Signals for quantum
    qsignal = any(s in tx for s in ["ψ", "rho", "ρ", "|", "unitary", "hamiltonian", "H", "U", "ket", "bra"]) 
    features["domain_signals"]["quantum"] = 1.0 if qsignal else 0.0

    # signals for electrical
    esignal = any(w in tx for w in ["ohm", "V=", "I=", "R=", "RC", "RL", "circuit"]) 
    features["domain_signals"]["electrical"] = 1.0 if esignal else 0.0

    # chemistry
    csignal = features["reaction_arrows"] or any(w in tx for w in ["Keq","k","molar","stoichiometry"]) 
    features["domain_signals"]["chemistry"] = 1.0 if csignal else 0.0

    # mechanics / algebra fallback signals
    features["domain_signals"]["physics.mechanics"] = 0.5 if any(w in tx for w in ["force","momentum","energy","m","v","g"]) else 0.0
    features["domain_signals"]["math.algebra"] = 0.5 if any(w in tx for w in ["matrix","det","trace","polynomial"]) else 0.0

    return features


def feature_vector(features: Dict[str, Any]) -> Dict[str, float]:
    # simple aggregator to pick top signals
    return features.get("domain_signals", {})
"""Core_Engines/Perception_Context.py

Lightweight Perception & Context extractor (PCX).
Provides basic API to extract context, meta-features and confidence scores from inputs.
"""
from typing import Dict, Any


class PerceptionContext:
    """Simple PCX scaffold.

    Methods:
        extract(input_data) -> {'context': {...}, 'meta': {...}, 'confidence': float}
    """
    def __init__(self, config: Dict[str, Any] = None): # type: ignore
        self.config = config or {}

    def extract(self, input_data: Any) -> Dict[str, Any]:
        """Extract a minimal context from input data.

        This is intentionally conservative: return a dict with 'context', 'meta', and 'confidence'.
        """
        # Basic heuristics for scaffold; real implementations will plug in NLP/vision modules
        ctx = {}
        meta = {}
        confidence = 0.5

        if input_data is None:
            return {'context': ctx, 'meta': meta, 'confidence': 0.0}

        # if input is a dict with fields, surface top-level keys as context hints
        if isinstance(input_data, dict):
            ctx = {k: v for k, v in input_data.items() if k in ('user', 'task', 'ts', 'source')}
            meta['keys'] = list(input_data.keys())[:10]
            confidence = 0.6
        else:
            # fallback: stringify
            s = str(input_data)
            meta['len'] = len(s)
            ctx['summary'] = s[:200]
            confidence = 0.4

        # simple quality heuristics
        meta['has_ts'] = bool(ctx.get('ts'))
        meta['source'] = ctx.get('source')

        return {'context': ctx, 'meta': meta, 'confidence': float(confidence)}
