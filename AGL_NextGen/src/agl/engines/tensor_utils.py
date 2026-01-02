"""Small, central tensor conversion helpers.

Provides:
 - to_numpy_safe(x)
 - to_torch_complex64(x)
 - matmul_safe(a, b)

These helpers attempt torch operations first and fall back to NumPy when
matmul or dtype/device operations fail (useful with stubbed torch in tests).
"""
from typing import Any


def safe_matmul(torch, A, B):
    # حاول أولاً الدالة الرسمية
    if hasattr(torch, "matmul"):
        try:
            return torch.matmul(A, B)
        except Exception:
            pass
    # بعض بدائل باك-إند تملك mm
    if hasattr(A, "mm"):
        try:
            return A.mm(B)
        except Exception:
            pass
    # محاولة أخيرة: قد تكون موجودة __matmul__
    try:
        return A @ B
    except Exception:
        pass
    # فشل على مستوى الواجهات; جرّب المسار الآمن الذي يستخدم NumPy/Scipy كملاذ
    try:
        return matmul_safe(A, B)
    except Exception:
        raise TypeError("Backend does not support matrix multiplication for these tensor types.")


def safe_sub(torch, X, Y):
    try:
        return X - Y
    except Exception:
        if hasattr(torch, "sub"):
            return torch.sub(X, Y)
        raise


def safe_dtype(x):
    # قد لا يملك dtype في الستاَب
    return getattr(x, "dtype", None)


def safe_zeros_like_dtype(torch, shape, ref):
    dt = safe_dtype(ref)
    if dt is not None:
        try:
            return torch.zeros(shape, dtype=dt)  # type: ignore
        except Exception:
            pass
    # fallback بدون dtype
    return torch.zeros(shape)

def to_numpy_safe(x: Any):
    """Return a NumPy ndarray view of x.

    - If x is a torch tensor, detach/cpu() then .numpy().
    - If x already has .numpy(), use it.
    - Otherwise try numpy.asarray(x).
    """
    try:
        import numpy as _np
        import torch as _torch
    except Exception:
        # minimal fallback if imports fail
        import numpy as _np

    # torch.Tensor case
    try:
        if 'torch' in globals() or 'torch' in locals():
            pass
    except Exception:
        pass

    # handle objects with numpy()
    try:
        if hasattr(x, 'detach') and hasattr(x, 'cpu') and hasattr(x, 'numpy'):
            return x.detach().cpu().numpy()
    except Exception:
        pass

    try:
        if hasattr(x, 'numpy'):
            return x.numpy()
    except Exception:
        pass

    # Use numpy.asarray but inspect dtype; if object-dtype, try to coerce
    try:
        arr = _np.asarray(x)
    except Exception:
        # last resort: convert via list
        try:
            arr = _np.array(list(x))
        except Exception:
            raise

    if arr.dtype == object:
        flat = []
        for el in arr.ravel():
            try:
                if hasattr(el, 'detach') and hasattr(el, 'cpu') and hasattr(el, 'numpy'):
                    flat.append(el.detach().cpu().numpy())
                elif hasattr(el, 'numpy'):
                    flat.append(el.numpy())
                elif hasattr(el, 'item'):
                    flat.append(el.item())
                elif hasattr(el, 'tolist'):
                    flat.append(_np.asarray(el.tolist()))
                else:
                    flat.append(_np.asarray(el))
            except Exception:
                try:
                    flat.append(_np.asarray(el))
                except Exception:
                    flat.append(el)
        try:
            return _np.asarray(flat).reshape(arr.shape)
        except Exception:
            return _np.asarray(flat)

    return arr


def to_torch_complex64(x: Any):
    """Convert x to a torch tensor with dtype torch.complex64 (best-effort).

    If torch isn't available, raise ImportError.
    """
    try:
        import torch as _torch
        import numpy as _np
    except Exception as e:
        raise ImportError('torch is required for to_torch_complex64') from e

    # If already a torch tensor, try to coerce dtype
    try:
        if hasattr(x, 'to'):
            return x.to(dtype=_torch.complex64)
    except Exception:
        pass

    # If it's a numpy array or array-like
    try:
        arr = _np.asarray(x)
        return _torch.from_numpy(arr.astype(_np.complex64)) # type: ignore
    except Exception:
        # fallback: try constructing from list
        return _torch.tensor(x, dtype=_torch.complex64)


def matmul_safe(a: Any, b: Any):
    """Matrix-multiply a and b, trying torch matmul then NumPy fallback.

    Returns a torch tensor if torch is available and the torch path succeeds;
    otherwise returns a NumPy ndarray.
    """
    # Try torch matmul first
    try:
        import torch as _torch
        # if both look like torch tensors, try operator
        if hasattr(a, '__matmul__') or hasattr(b, '__matmul__'):
            try:
                return a @ b
            except Exception:
                pass
    except Exception:
        _torch = None

    # NumPy fallback
    import numpy as _np

    a_np = to_numpy_safe(a)
    b_np = to_numpy_safe(b)
    res = _np.matmul(a_np, b_np)

    # If torch is available, try to convert back
    try:
        if _torch is not None:
            return to_torch_complex64(res)
    except Exception:
        pass

    return res
