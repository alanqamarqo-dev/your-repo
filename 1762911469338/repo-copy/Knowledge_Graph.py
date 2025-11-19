# Compatibility shim for legacy `import Knowledge_Graph`
# Prefers Knowledge_Base.Knowledge_Graph, falls back to Self_Improvement.Knowledge_Graph.

try:
    from Knowledge_Base.Knowledge_Graph import *  # type: ignore
    try:
        from Knowledge_Base.Knowledge_Graph import __all__ as __all__  # type: ignore
    except Exception:
        pass
except ModuleNotFoundError:
    from Self_Improvement.Knowledge_Graph import *  # type: ignore
    try:
        from Self_Improvement.Knowledge_Graph import __all__ as __all__  # type: ignore
    except Exception:
        # Derive a best-effort __all__ if not exported upstream
        __all__ = [n for n in globals() if not n.startswith("_")]

# NOTE: Do not perform factory registrations here; registration occurs inside upstream modules.
