from Integration_Layer.Domain_Router import get_engine

# fallback mappings for single-step alternatives
FALLBACKS = {
    ("nlp", "extract_query"): [("nlp", "understand")],
    ("knowledge", "answer"):  [("creative", "explain_like_im_five")],
    ("strategic", "plan"):    [("creative", "structured_brainstorm")],
    ("visual", "describe_or_generate"): [("nlp", "describe_textually")],
    ("social", "empathetic_reply"): [("nlp", "polite_reply")],
}


def _call_step(engine_name: str, method: str, ctx: dict):
    eng = get_engine(engine_name)
    fn = getattr(eng, method, None)
    if fn is None:
        raise AttributeError(f"{engine_name}.{method} not found")
    return fn(ctx)


def execute_pipeline(pipeline, context):
    out = context or {}
    for engine_name, method in pipeline:
        try:
            out = _call_step(engine_name, method, out)
        except Exception:
            # try fallbacks for the single step
            for fb_engine, fb_method in FALLBACKS.get((engine_name, method), []):
                try:
                    out = _call_step(fb_engine, fb_method, out)
                    break
                except Exception:
                    continue
            else:
                out = {**out, "warning": f"{engine_name}.{method} failed; fallback exhausted."}
                continue
    return out
