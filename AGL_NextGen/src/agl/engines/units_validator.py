class UnitsValidator:
    def __init__(self, **kwargs):
        self.name = "Units_Validator"

    @staticmethod
    def create_engine(config=None):
        return UnitsValidator()

    def process_task(self, payload: dict):
        # very small validator: checks for unit-like strings
        text = str(payload.get("text") or payload.get("value") or "")
        ok = any(u in text for u in ["m", "kg", "s", "km", "cm"]) if text else False
        return {"ok": True, "engine": "units_validator:stub", "valid": ok}
import re
from collections import Counter

_DIM_TOKEN = re.compile(r"([a-zA-Z]+)(\^(-?\d+))?")

def _parse_dim(expr):
    expr = expr.replace(" ", "")
    if not expr:
        return Counter()
    num, *den = expr.split("/")
    def mult_side(side):
        c = Counter()
        if side == "":
            return c
        for part in side.split("*"):
            if not part:
                continue
            m = _DIM_TOKEN.fullmatch(part)
            if not m:
                raise ValueError(f"Bad dimension token: {part}")
            base = m.group(1)
            pow_ = int(m.group(3) or "1")
            c[base] += pow_
        return c
    out = mult_side(num)
    if den:
        d = "/".join(den)
        out -= mult_side(d)
    for k in list(out.keys()):
        if out[k] == 0:
            del out[k]
    return out

def _combine_dim_of_symbols(symbols, dims_map):
    c = Counter()
    op = "*"
    for tok in symbols:
        if tok in ("*", "/"):
            op = tok
            continue
        dim_str = dims_map.get(tok, "")
        part = _parse_dim(dim_str)
        if op == "*":
            c += part
        else:
            c -= part
    for k in list(c.keys()):
        if c[k] == 0:
            del c[k]
    return c

def check_dimensional_consistency(lhs_tokens, rhs_tokens, dims_map):
    lhs = _combine_dim_of_symbols(lhs_tokens, dims_map)
    rhs = _combine_dim_of_symbols(rhs_tokens, dims_map)
    return lhs == rhs

