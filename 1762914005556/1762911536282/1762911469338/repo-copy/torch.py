"""Project-local shim to expose `stubs.torch` as `torch` for imports.
This file provides a minimal, robust `zeros` implementation compatible
with calls like `torch.zeros((n, n))` used in the codebase.
"""
from stubs import torch as _torch

# delegate core functions to the stub when present
norm = getattr(_torch, 'norm')
norm = getattr(_torch, 'norm')
_eye = getattr(_torch, 'eye')
Tensor = getattr(_torch, 'Tensor', object)
linalg = getattr(_torch, 'linalg')

# dtype placeholders used in the codebase
complex64 = 'complex64'


def eye(n, dtype=None, device=None):
	# support dtype argument but ignore it in the stub
	return _eye(n)


def _ensure_tensor_like(x):
	# If x is already a Tensor-like object from our zeros implementation, return as-is
	# We check for internal marker attributes rather than duck-typing lists.
	if hasattr(x, '_data') or hasattr(x, 'shape') and hasattr(x, '__setitem__'):
		return x
	# If x is a nested list, wrap it into our Tensor-like class
	if isinstance(x, list):
		rows = len(x)
		cols = len(x[0]) if rows > 0 and isinstance(x[0], list) else 1
		t = zeros((rows, cols))
		for i in range(rows):
			for j in range(cols):
				t[i, j] = x[i][j] if isinstance(x[i], list) else x[i]
		return t
	# Fallback: wrap scalar
	t = zeros((1, 1))
	t[0, 0] = x
	return t


def tensor(x, dtype=None):
	return _ensure_tensor_like(x)


def _py_zeros(shape, dtype=float):
	# Normalize shape to a tuple
	if isinstance(shape, int):
		shape = (shape,)
	elif isinstance(shape, tuple):
		shape = tuple(shape)
	else:
		shape = (1,)

	class _TensorLike:
		def __init__(self, shape_tuple):
			self._shape = tuple(shape_tuple)
			self._size = 1
			for s in self._shape:
				self._size *= s
			self._flat = [0.0] * self._size

		@property
		def shape(self):
			return self._shape

		def _flat_index(self, idx):
			if isinstance(idx, int):
				return idx
			if not isinstance(idx, tuple):
				raise IndexError('Invalid index')
			# handle negative indices
			idx = tuple(i if i >= 0 else self._shape[k] + i for k, i in enumerate(idx))
			if len(idx) != len(self._shape):
				raise IndexError('Index dimension mismatch')
			pos = 0
			mul = 1
			for dim, i in reversed(list(zip(self._shape, idx))):
				pos = pos + i * mul
				mul *= dim
			return pos

		def __getitem__(self, idx):
			if isinstance(idx, tuple):
				pos = self._flat_index(idx)
				return self._flat[pos]
			if isinstance(idx, int):
				if len(self._shape) == 1:
					return self._flat[idx]
				# return a view representing that slice
				new_shape = self._shape[1:]
				stride = 1
				for s in new_shape:
					stride *= s
				start = idx * stride
				slice_vals = self._flat[start:start+stride]
				t = _TensorLike(new_shape)
				t._flat = slice_vals.copy()
				return t
			raise IndexError('Unsupported index type')

		def __setitem__(self, idx, val):
			if isinstance(idx, tuple):
				pos = self._flat_index(idx)
				self._flat[pos] = val
				return
			if isinstance(idx, int):
				if len(self._shape) == 1:
					self._flat[idx] = val
					return
			raise IndexError('Unsupported index type for setitem')

		def tolist(self):
			def _build(flat, shape):
				if len(shape) == 1:
					return flat.copy()
				size = 1
				for s in shape[1:]:
					size *= s
				return [_build(flat[i*size:(i+1)*size], shape[1:]) for i in range(shape[0])]
			return _build(self._flat, list(self._shape))

		def __repr__(self):
			return f"Tensor(shape={self._shape})"

		def __mul__(self, other):
			if isinstance(other, (int, float, complex)):
				r = _TensorLike(self._shape)
				r._flat = [v * other for v in self._flat]
				return r
			raise TypeError('Unsupported multiplication')

		def __rmul__(self, other):
			return self.__mul__(other)

		def view(self, *newshape):
			newshape = list(newshape)
			if len(newshape) == 0:
				newshape = [1]
			if -1 in newshape:
				idx = newshape.index(-1)
				known = 1
				for s in newshape:
					if s != -1:
						known *= s
				newshape[idx] = self._size // known
			prod = 1
			for s in newshape:
				prod *= s
			if prod != self._size:
				return _TensorLike(tuple(newshape))
			t = _TensorLike(tuple(newshape))
			t._flat = self._flat.copy()
			return t

		def clone(self):
			t = _TensorLike(self._shape)
			t._flat = self._flat.copy()
			return t

		def transpose(self, a, b):
			if len(self._shape) < 2:
				return self
			r, c = self._shape[0], self._shape[1]
			out = _TensorLike((c, r))
			for i in range(r):
				for j in range(c):
					out[j, i] = self[i, j]
			return out

		def abs(self):
			t = _TensorLike(self._shape)
			t._flat = [abs(v) for v in self._flat]
			return t

		def __pow__(self, other):
			t = _TensorLike(self._shape)
			t._flat = [v ** other for v in self._flat]
			return t

	return _TensorLike(tuple(shape))


zeros = getattr(_torch, 'zeros', _py_zeros)
zeros_like = getattr(_torch, 'zeros_like', lambda x: zeros(getattr(x, 'shape', (1,))))

__all__ = ['norm', 'eye', 'Tensor', 'linalg', 'zeros', 'zeros_like']

# Additional helpers used by core engines
def kron(a, b):
	# simple Kronecker product for our Tensor-like objects or lists
	A = a._data if hasattr(a, '_data') else a
	B = b._data if hasattr(b, '_data') else b
	a_rows = len(A)
	a_cols = len(A[0]) if a_rows else 0
	b_rows = len(B)
	b_cols = len(B[0]) if b_rows else 0
	result = [[0.0 for _ in range(a_cols * b_cols)] for _ in range(a_rows * b_rows)]
	for i in range(a_rows):
		for j in range(a_cols):
			for p in range(b_rows):
				for q in range(b_cols):
					result[i * b_rows + p][j * b_cols + q] = A[i][j] * B[p][q]
	return _ensure_tensor_like(result)


def trace(m):
	M = m._data if hasattr(m, '_data') else m
	return sum(M[i][i] for i in range(len(M)))


def stack(list_of_mats):
	# simple vertical stack into a list for demos
	return list_of_mats


def all(x):
	# simple truth check: non-zero entries
	if hasattr(x, '_data'):
		return all(any(cell for cell in row) for row in x._data)
	return bool(x)

def tensor_clone(x):
	return _ensure_tensor_like(x)

def tensor_like_zeros(x):
	return zeros_like(x)


# --- Minimal `nn` shim ---
import math
import random


def _to_native_list(t):
	# Convert our Tensor-like or nested lists to native nested lists
	if hasattr(t, 'tolist'):
		return t.tolist()
	if isinstance(t, list):
		return t
	return [[t]]


def _from_native_list(lst):
	return _ensure_tensor_like(lst)


def randn(shape):
	# Return a Tensor-like filled with small random floats
	if isinstance(shape, int):
		shape = (shape,)
	t = zeros(shape)
	# fill flat storage if available
	if hasattr(t, '_flat'):
		for i in range(len(t._flat)):
			t._flat[i] = (random.random() - 0.5) * 0.01
	return t


def randn_like(x):
	return randn(getattr(x, 'shape', (1,)))


def softmax(x, dim=-1):
	# Very small softmax for 1-D or last-dim vector-like tensors
	lst = _to_native_list(x)
	# Handle 1D vectors represented as [v1, v2, ...]
	if isinstance(lst[0], list):
		# matrix-like: apply on last axis for each row
		out = []
		for row in lst:
			exps = [math.exp(v) for v in row]
			s = sum(exps) or 1.0
			out.append([e / s for e in exps])
		return _from_native_list(out)
	else:
		exps = [math.exp(v) for v in lst] # type: ignore
		s = sum(exps) or 1.0
		return _from_native_list([e / s for e in exps])


class _NNModuleBase:
	"""Simple base class for nn modules in our shim."""
	def __init__(self):
		self._parameters = {}

	def parameters(self):
		return list(self._parameters.values())

	def __call__(self, x):
		return self.forward(x) # type: ignore


class Linear(_NNModuleBase):
	def __init__(self, in_features, out_features, bias=True):
		super().__init__()
		# weights: out_features x in_features
		self.in_features = in_features
		self.out_features = out_features
		self.weight = zeros((out_features, in_features))
		self.bias = zeros((out_features,)) if bias else None
		self._parameters['weight'] = self.weight
		if bias:
			self._parameters['bias'] = self.bias

	def forward(self, x):
		# x can be Tensor-like of shape (batch, in_features) or (in_features,)
		native = _to_native_list(x)
		# Normalize representation to list of rows
		if not native:
			return zeros((0, self.out_features))
		if not isinstance(native[0], list):
			rows = [native]
		else:
			rows = native

		W = _to_native_list(self.weight)
		B = _to_native_list(self.bias) if self.bias is not None else None
		out = []
		for r in rows:
			row_out = []
			for j in range(self.out_features):
				s = 0.0
				for i in range(self.in_features):
					vi = r[i] if i < len(r) else 0.0
					s += vi * (W[j][i] if j < len(W) and i < len(W[j]) else 0.0) # type: ignore
				if B is not None:
					s += (B[j] if j < len(B) else 0.0) # type: ignore
				row_out.append(s)
			out.append(row_out)
		# Collapse single-row outputs to 1D
		if len(out) == 1:
			return _from_native_list(out[0])
		return _from_native_list(out)


class ReLU(_NNModuleBase):
	def __init__(self):
		super().__init__()

	def forward(self, x):
		lst = _to_native_list(x)
		def apply_relu(val):
			if isinstance(val, list):
				return [apply_relu(v) for v in val]
			return max(0.0, val)
		return _from_native_list(apply_relu(lst))


class Sequential(_NNModuleBase):
	def __init__(self, *modules):
		super().__init__()
		self.modules = list(modules)

	def forward(self, x):
		out = x
		for m in self.modules:
			out = m(out)
		return out


class _NNNamespace:
	def __init__(self):
		self.Module = _NNModuleBase
		self.Linear = Linear
		self.Sequential = Sequential
		self.ReLU = ReLU


# attach nn namespace to module
nn = _NNNamespace()

# expose a few top-level helpers commonly used
__all__.extend(['kron', 'trace', 'stack', 'all', 'tensor_clone', 'tensor_like_zeros', 'nn', 'randn', 'randn_like', 'softmax'])
