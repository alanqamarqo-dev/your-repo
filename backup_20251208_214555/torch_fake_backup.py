"""Minimal project-local torch shim.
Tries to import the real `torch` from site-packages. If that fails,
it falls back to a tiny stub from `stubs.torch` and provides a few
attributes the codebase expects (dtypes and `__version__`).

This file intentionally keeps the fallback minimal and well-formatted
to avoid shadowing a real PyTorch installation or causing syntax errors.
"""
import sys
import os
import importlib

# Prefer the installed torch. Remove this file's directory from sys.path to
# avoid importing the local shim when resolving the installed package.
_this_dir = os.path.dirname(__file__)
if _this_dir in sys.path:
    try:
        sys.path.remove(_this_dir)
    except ValueError:
        pass

try:
    # First, try to locate a torch package inside site-packages manually. This
    # avoids recursively importing this local module when Python would otherwise
    # pick up this file.
    import importlib.util
    import sysconfig
    import site

    found = None
    candidates = []
    for key in ("purelib", "platlib"):
        p = sysconfig.get_paths().get(key)
        if p:
            candidates.append(p)
    try:
        candidates.extend(site.getsitepackages())
    except Exception:
        pass
    try:
        users = site.getusersitepackages()
        if users:
            candidates.append(users)
    except Exception:
        pass

    # Deduplicate while preserving order
    seen = set()
    uniq = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            uniq.append(c)

    for p in uniq:
        candidate = os.path.join(p, "torch")
        init_py = os.path.join(candidate, "__init__.py")
        if os.path.isdir(candidate) and os.path.isfile(init_py):
            spec = importlib.util.spec_from_file_location("torch", init_py)
            if spec is not None and spec.loader is not None:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                sys.modules["torch"] = mod
                sys.modules[__name__] = mod
                found = mod
                break
    if found is None:
        # As a last resort attempt a normal import but ensure the current
        # shim does not block discovery: temporarily remove 'torch' from
        # sys.modules and restore it on failure.
        saved = sys.modules.pop("torch", None)
        try:
            _real_torch = importlib.import_module("torch")
            # If successful, replace this module with the real torch.
            if getattr(_real_torch, "__file__", None) != __file__:
                sys.modules[__name__] = _real_torch
                sys.modules["torch"] = _real_torch
            else:
                # import produced this shim again; treat as failure
                raise ImportError("imported torch is this shim")
        except Exception:
            # restore any saved module and re-raise
            if saved is not None:
                sys.modules["torch"] = saved
            raise ImportError("site-packages torch not found via search or import")
except Exception:
    # Real torch not available, fall back to repo-local stub under stubs/torch.py
    from stubs import torch as _torch

    __version__ = getattr(_torch, "__version__", "0.0.0-stub")
    int64 = getattr(_torch, "int64", "int64")
    int32 = getattr(_torch, "int32", "int32")
    float32 = getattr(_torch, "float32", "float32")

    def zeros(shape):
        if isinstance(shape, int):
            shape = (shape,)
        if not isinstance(shape, tuple):
            shape = tuple(shape)
        if len(shape) == 0:
            return 0
        if len(shape) == 1:
            return [0.0 for _ in range(shape[0])]
        if len(shape) == 2:
            rows, cols = shape
            return [[0.0 for _ in range(cols)] for _ in range(rows)]
        # higher dims: nested lists
        def build(s):
            if len(s) == 1:
                return [0.0 for _ in range(s[0])]
            return [build(s[1:]) for _ in range(s[0])]

        return build(list(shape))

    def tensor(x, dtype=None):
        return x

    norm = getattr(_torch, "norm", None)
    eye = getattr(_torch, "eye", lambda n: zeros((n, n)))
    Tensor = getattr(_torch, "Tensor", object)
    linalg = getattr(_torch, "linalg", None)

    class _NNNamespace:
        def __init__(self):
            self.Module = object

    nn = _NNNamespace()

    zeros_like = getattr(_torch, "zeros_like", lambda x: zeros(getattr(x, "shape", (1,))))
    __all__ = [
        "__version__",
        "int64",
        "int32",
        "float32",
        "zeros",
        "tensor",
        "norm",
        "eye",
        "Tensor",
        "linalg",
        "nn",
        "zeros_like",
    ]
