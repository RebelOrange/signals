import numpy as np
from fxpmath import Fxp

DEFAULT_MARKER = object()
HANDLED_FUNCTIONS = {}

def implements(numpy_function):
    """Decorator to register custom fixed-point overrides for NumPy functions."""
    def decorator(func):
        HANDLED_FUNCTIONS[numpy_function] = func
        return func
    return decorator


class ap_fixed:
    # Set to True to retain LHS precision (Vitis HLS register behavior),
    # or False for dynamic bit-growth modeling.
    PRESERVE_LHS_PRECISION = True

    QUANT_MAP = {
        'AP_TRN': 'bit_trunc',            # Truncation to -inf (Default)
        'AP_TRN_ZERO': 'trunc',           # Truncation to zero
        'AP_RND': 'nearest_posinf',       # Round ties to +inf
        'AP_RND_ZERO': 'nearest_zero',     # Round ties to zero
        'AP_RND_INF': 'nearest_away',     # Round ties away from zero (+/- inf)
        'AP_RND_MIN_INF': 'nearest_neginf',# Round ties to -inf
        'AP_RND_CONVERGENT': 'around'     # Round ties to nearest even (Banker's)
    }

    # All 5 Vitis HLS Overflow Modes
    OVERFLOW_MAP = {
        'AP_WRAP': 'wrap',                # Two's complement wrap (Default)
        'AP_SAT': 'saturate',             # Saturation [-MIN, MAX]
        'AP_SAT_ZERO': 'custom_sat_zero', # Saturation to zero
        'AP_SAT_SYM': 'custom_sat_sym',   # Symmetrical saturation [-MAX, MAX]
        'AP_WRAP_SM': 'custom_wrap_sm'    # Sign-magnitude wrap
    }

    def __init__(self, W=16, I=4, val=DEFAULT_MARKER, mode='AP_TRN', overflow='AP_WRAP', template=None):
        self.W, self.I, val_data, self.mode, self.overflow = self._parse_args(
            W, I, val, mode, overflow, template
        )
        self.F = self.W - self.I
        self._orig_val = val_data
        self._update_val(val_data)

    @staticmethod
    def _parse_args(W, I, val, mode, overflow, template):
        if template is not None:
            val_data = W if val is DEFAULT_MARKER else val
            return int(template.W), int(template.I), val_data, template.mode, template.overflow

        if hasattr(W, 'W') and hasattr(W, 'I'):
            t = W
            val_data = I if val is DEFAULT_MARKER else val
            return int(t.W), int(t.I), val_data, t.mode, t.overflow

        if not isinstance(W, (int, np.integer)):
            return 16, 4, W, mode, overflow

        val_data = 0.0 if val is DEFAULT_MARKER else val
        return int(W), int(I), val_data, mode, overflow

    def _update_val(self, val):
        raw_val = val.to_float() if isinstance(val, ap_fixed) else val
        val_arr = np.asarray(raw_val, dtype=np.float64)

        if val_arr.size == 0:
            self._empty_shape = val_arr.shape
            self._fxp = Fxp(0.0, signed=True, n_word=self.W, n_frac=self.F, overflow='wrap', rounding='bit_trunc')
            return

        self._empty_shape = None
        fxp_round = self.QUANT_MAP.get(self.mode, 'bit_trunc')
        fxp_overflow = self.OVERFLOW_MAP.get(self.overflow, 'wrap')

        if fxp_overflow in ('wrap', 'saturate'):
            self._fxp = Fxp(
                val=val_arr,
                signed=True,
                n_word=self.W,
                n_frac=self.F,
                overflow=fxp_overflow,
                rounding=fxp_round
            )
        else:
            temp_fxp = Fxp(val=val_arr, signed=True, n_word=self.W, n_frac=self.F, overflow='wrap', rounding=fxp_round)
            quantized_val = temp_fxp.get_val()

            max_val = (2 ** (self.I - 1)) - (2 ** (-self.F))
            min_val = -(2 ** (self.I - 1))

            if self.overflow == 'AP_SAT_ZERO':
                mask_overflow = (quantized_val > max_val) | (quantized_val < min_val)
                quantized_val = np.where(mask_overflow, 0.0, quantized_val)
            elif self.overflow == 'AP_SAT_SYM':
                sym_min = -max_val
                quantized_val = np.clip(quantized_val, sym_min, max_val)
            elif self.overflow == 'AP_WRAP_SM':
                sign = np.sign(quantized_val)
                abs_val = np.abs(quantized_val)
                scale = 2 ** self.F
                raw_mag = np.floor(abs_val * scale).astype(np.int64)
                modulus = 1 << (self.W - 1)
                wrapped_mag = raw_mag % modulus
                quantized_val = sign * (wrapped_mag / scale)

            self._fxp = Fxp(val=quantized_val, signed=True, n_word=self.W, n_frac=self.F, overflow='wrap',
                            rounding='bit_trunc')

    def __getitem__(self, key) -> 'ap_fixed':
        val_slice = self.to_float()[key]
        return ap_fixed(template=self, val=val_slice)

    def flatten(self, order='F') -> 'ap_fixed':
        flat_val = self.to_float().flatten(order=order)
        return ap_fixed(template=self, val=flat_val)

    def __setitem__(self, key, value):
        val_to_set = value.to_float() if isinstance(value, ap_fixed) else np.asarray(value)
        curr_arr = np.array(self.to_float(), copy=True)
        curr_arr[key] = val_to_set
        self._update_val(curr_arr)

    def assign(self, val) -> 'ap_fixed':
        self._orig_val = val
        self._update_val(val)
        return self

    def __ilshift__(self, other) -> 'ap_fixed':
        self._orig_val = other
        self._update_val(other)
        return self

    def typedef(self, type_template) -> 'ap_fixed':
        src = self._orig_val if hasattr(self, '_orig_val') and self._orig_val is not DEFAULT_MARKER else self.to_float()
        return ap_fixed(template=type_template, val=src)

    def cast(self, W, I, mode=None, overflow=None) -> 'ap_fixed':
        m = mode or self.mode
        o = overflow or self.overflow
        return ap_fixed(W, I, self.to_float(), mode=m, overflow=o)

    def __call__(self, val, **kwargs) -> 'ap_fixed':
        m = kwargs.get('mode', self.mode)
        o = kwargs.get('overflow', self.overflow)
        return ap_fixed(self.W, self.I, val, mode=m, overflow=o)

    def matmul(self, other, out: 'ap_fixed' = None) -> 'ap_fixed':
        res = self @ other
        if out is not None:
            out <<= res
            return out
        return res

    def to_float(self) -> np.ndarray:
        if getattr(self, '_empty_shape', None) is not None:
            return np.empty(self._empty_shape, dtype=np.float64)
        return self._fxp.get_val()

    def raw(self) -> np.ndarray:
        if getattr(self, '_empty_shape', None) is not None:
            return np.empty(self._empty_shape, dtype=np.int64)
        return self._fxp.raw()

    @property
    def shape(self):
        if getattr(self, '_empty_shape', None) is not None:
            return self._empty_shape
        return self._fxp.val.shape if isinstance(self._fxp.val, np.ndarray) else ()

    def reshape(self, *shape, order='C') -> 'ap_fixed':
        """Reshapes the fixed-point array while preserving word lengths and quantization modes.

        Supports both tuple shapes: arr.reshape((1, N)) and unpacked shapes: arr.reshape(1, N).
        """
        if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
            new_shape = shape[0]
        else:
            new_shape = shape

        reshaped_val = self.to_float().reshape(new_shape, order=order)
        return ap_fixed(template=self, val=reshaped_val)

    # --- Matrix Multiplication (@) ---
    def __matmul__(self, other) -> 'ap_fixed':
        if hasattr(other, 'to_complex') or np.iscomplexobj(other):
            return NotImplemented
        other_obj = other if isinstance(other, ap_fixed) else ap_fixed(template=self, val=other)
        res_float = self.to_float() @ other_obj.to_float()

        if self.PRESERVE_LHS_PRECISION:
            return ap_fixed(template=self, val=res_float)

        K = self.shape[-1] if len(self.shape) > 0 else 1
        accum_bits = int(np.ceil(np.log2(K))) if K > 1 else 0

        new_I = self.I + other_obj.I + accum_bits
        new_W = self.W + other_obj.W + accum_bits
        return ap_fixed(new_W, new_I, res_float, mode=self.mode, overflow=self.overflow)

    def __rmatmul__(self, other) -> 'ap_fixed':
        if hasattr(other, 'to_complex') or np.iscomplexobj(other):
            return NotImplemented
        other_obj = ap_fixed(template=self, val=other)
        return other_obj @ self

    def __imatmul__(self, other) -> 'ap_fixed':
        res = self @ other
        self.assign(res.to_float())
        return self

    def __truediv__(self, other) -> 'ap_fixed':
        if hasattr(other, 'to_complex') or np.iscomplexobj(other):
            return NotImplemented
        if isinstance(other, ap_fixed):
            other_val = other.to_float()
            other_I, other_F = other.I, other.F
        else:
            other_val = np.asarray(other, dtype=np.float64)
            other_I, other_F = self.I, self.F

        res_val = self.to_float() / other_val

        if self.PRESERVE_LHS_PRECISION:
            return ap_fixed(template=self, val=res_val)

        new_I = self.I + other_F
        new_F = self.F + other_I
        new_W = new_I + new_F
        return ap_fixed(new_W, new_I, res_val, mode=self.mode, overflow=self.overflow)

    def __rtruediv__(self, other) -> 'ap_fixed':
        if hasattr(other, 'to_complex') or np.iscomplexobj(other):
            return NotImplemented
        other_obj = ap_fixed(template=self, val=other)
        return other_obj / self

    def __itruediv__(self, other) -> 'ap_fixed':
        res = self / other
        self.assign(res.to_float())
        return self

    # --- Elementwise Arithmetic ---
    def __add__(self, other) -> 'ap_fixed':
        if hasattr(other, 'to_complex') or np.iscomplexobj(other):
            return NotImplemented
        other_obj = other if isinstance(other, ap_fixed) else ap_fixed(template=self, val=other)
        res_val = self.to_float() + other_obj.to_float()

        if self.PRESERVE_LHS_PRECISION:
            return ap_fixed(template=self, val=res_val)

        new_I = max(self.I, other_obj.I) + 1
        new_F = max(self.F, other_obj.F)
        new_W = new_I + new_F
        return ap_fixed(new_W, new_I, res_val, mode=self.mode, overflow=self.overflow)

    def __radd__(self, other) -> 'ap_fixed':
        return self.__add__(other)

    def __iadd__(self, other) -> 'ap_fixed':
        res = self + other
        self.assign(res.to_float())
        return self

    def __sub__(self, other) -> 'ap_fixed':
        if hasattr(other, 'to_complex') or np.iscomplexobj(other):
            return NotImplemented
        other_obj = other if isinstance(other, ap_fixed) else ap_fixed(template=self, val=other)
        res_val = self.to_float() - other_obj.to_float()

        if self.PRESERVE_LHS_PRECISION:
            return ap_fixed(template=self, val=res_val)

        new_I = max(self.I, other_obj.I) + 1
        new_F = max(self.F, other_obj.F)
        new_W = new_I + new_F
        return ap_fixed(new_W, new_I, res_val, mode=self.mode, overflow=self.overflow)

    def __rsub__(self, other) -> 'ap_fixed':
        if hasattr(other, 'to_complex') or np.iscomplexobj(other):
            return NotImplemented
        other_obj = ap_fixed(template=self, val=other)
        return other_obj - self

    def __isub__(self, other) -> 'ap_fixed':
        res = self - other
        self.assign(res.to_float())
        return self

    def __mul__(self, other) -> 'ap_fixed':
        if hasattr(other, 'to_complex') or np.iscomplexobj(other):
            return NotImplemented
        other_obj = other if isinstance(other, ap_fixed) else ap_fixed(template=self, val=other)
        res_val = self.to_float() * other_obj.to_float()

        if self.PRESERVE_LHS_PRECISION:
            return ap_fixed(template=self, val=res_val)

        new_W = self.W + other_obj.W
        new_I = self.I + other_obj.I
        return ap_fixed(new_W, new_I, res_val, mode=self.mode, overflow=self.overflow)

    def __rmul__(self, other) -> 'ap_fixed':
        return self.__mul__(other)

    def __imul__(self, other) -> 'ap_fixed':
        res = self * other
        self.assign(res.to_float())
        return self

    def __neg__(self) -> 'ap_fixed':
        return ap_fixed(template=self, val=-self.to_float())

    def __pos__(self) -> 'ap_fixed':
        return self

    def __repr__(self):
        return f"ap_fixed<{self.W},{self.I},{self.mode},{self.overflow}>\n{self.to_float()}"

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        if method != '__call__':
            return NotImplemented
        raw_args = tuple(x.to_float() if isinstance(x, ap_fixed) else x for x in inputs)
        result = ufunc(*raw_args, **kwargs)
        if isinstance(result, np.ndarray):
            return ap_fixed(template=self, val=result)
        return result

    def __array_function__(self, func, types, args, kwargs):
        if func in HANDLED_FUNCTIONS:
            return HANDLED_FUNCTIONS[func](*args, **kwargs)
        raw_args = tuple(a.to_float() if isinstance(a, ap_fixed) else a for a in args)
        res = func(*raw_args, **kwargs)
        if isinstance(res, np.ndarray):
            return ap_fixed(template=self, val=res)
        return res

    def item(self, *args):
        return self.to_float().item(*args)

    def squeeze(self, axis=None) -> 'ap_fixed':
        squeezed_val = self.to_float().squeeze(axis=axis)
        return ap_fixed(template=self, val=squeezed_val)


@implements(np.vdot)
def vdot(a, b):
    a_cplx = a if hasattr(a, 'conj') else np.asarray(a)
    b_cplx = b if hasattr(b, 'to_float') else np.asarray(b)
    res = (a_cplx.conj() * b_cplx).sum()
    return res

@implements(np.abs)
def abs_fixed(x):
    val = np.abs(x.to_float() if hasattr(x, 'to_float') else x)
    return ap_fixed(template=x if hasattr(x, 'W') else None, val=val)


class ap_complex:
    PRESERVE_LHS_PRECISION = True

    def __init__(self, W=16, I=4, val=DEFAULT_MARKER, mode='AP_TRN', overflow='AP_WRAP', template=None):
        self.W, self.I, val_data, self.mode, self.overflow = ap_fixed._parse_args(
            W, I, val, mode, overflow, template
        )
        val_arr = np.zeros((), dtype=np.complex128) if val_data is DEFAULT_MARKER else np.asarray(val_data, dtype=np.complex128)
        self._orig_val = val_data

        self.real = ap_fixed(self.W, self.I, val_arr.real, mode=self.mode, overflow=self.overflow)
        self.imag = ap_fixed(self.W, self.I, val_arr.imag, mode=self.mode, overflow=self.overflow)

    def __getitem__(self, key) -> 'ap_complex':
        val_slice = self.to_complex()[key]
        return ap_complex(template=self, val=val_slice)

    def flatten(self, order='F') -> 'ap_complex':
        flat_val = self.to_complex().flatten(order=order)
        return ap_complex(template=self, val=flat_val)

    def __setitem__(self, key, value):
        if isinstance(value, ap_complex):
            val_complex = value.to_complex()
        elif isinstance(value, ap_fixed):
            val_complex = value.to_float().astype(np.complex128)
        else:
            val_complex = np.asarray(value, dtype=np.complex128)

        curr_arr = np.array(self.to_complex(), copy=True)
        curr_arr[key] = val_complex
        self._update_val(curr_arr)

    def to_complex(self) -> np.ndarray:
        return self.real.to_float() + 1j * self.imag.to_float()

    def item(self, *args):
        return self.to_complex().item(*args)

    def raw(self) -> dict:
        return {'real': self.real.raw(), 'imag': self.imag.raw()}

    def _update_val(self, val):
        val_arr = val.to_complex() if isinstance(val, ap_complex) else np.asarray(val, dtype=np.complex128)
        self.real = ap_fixed(self.W, self.I, val_arr.real, self.mode, self.overflow)
        self.imag = ap_fixed(self.W, self.I, val_arr.imag, self.mode, self.overflow)

    def assign(self, val) -> 'ap_complex':
        self._orig_val = val
        self._update_val(val)
        return self

    def __ilshift__(self, other) -> 'ap_complex':
        self._orig_val = other
        self._update_val(other)
        return self

    def squeeze(self, axis=None) -> 'ap_complex':
        squeezed_val = self.to_complex().squeeze(axis=axis)
        return ap_complex(template=self, val=squeezed_val)

    def typedef(self, type_template) -> 'ap_complex':
        src = self._orig_val if hasattr(self, '_orig_val') and self._orig_val is not DEFAULT_MARKER else self.to_complex()
        return ap_complex(template=type_template, val=src)

    def cast(self, W, I, mode=None, overflow=None) -> 'ap_complex':
        m = mode or self.mode
        o = overflow or self.overflow
        return ap_complex(W, I, self.to_complex(), mode=m, overflow=o)

    def __call__(self, val, **kwargs) -> 'ap_complex':
        m = kwargs.get('mode', self.mode)
        o = kwargs.get('overflow', self.overflow)
        return ap_complex(self.W, self.I, val, mode=m, overflow=o)

    def matmul(self, other, out: 'ap_complex' = None) -> 'ap_complex':
        res = self @ other
        if out is not None:
            out <<= res
            return out
        return res

    def conj(self) -> 'ap_complex':
        r = np.real(self.to_complex())
        im = np.imag(self.to_complex())
        return ap_complex(template=self, val=r - 1j * im)

    def conjugate(self) -> 'ap_complex':
        return self.conj()

    @property
    def T(self) -> 'ap_complex':
        return ap_complex(template=self, val=self.to_complex().T)

    @property
    def shape(self):
        return self.real.shape

    def reshape(self, *shape, order='C') -> 'ap_complex':
        """Reshapes the complex fixed-point array while preserving word lengths and quantization modes.

        Supports both tuple shapes: arr.reshape((1, N)) and unpacked shapes: arr.reshape(1, N).
        """
        if len(shape) == 1 and isinstance(shape[0], (tuple, list)):
            new_shape = shape[0]
        else:
            new_shape = shape

        reshaped_val = self.to_complex().reshape(new_shape, order=order)
        return ap_complex(template=self, val=reshaped_val)

    # --- Complex Matrix Multiplication & Arithmetic ---
    def __add__(self, other) -> 'ap_complex':
        other_val = other.to_complex() if isinstance(other, ap_complex) else (
            other.to_float() if isinstance(other, ap_fixed) else np.asarray(other, dtype=np.complex128))
        res = self.to_complex() + other_val

        if self.PRESERVE_LHS_PRECISION:
            return ap_complex(template=self, val=res)

        other_I = getattr(other, 'I', self.I)
        new_I = max(self.I, other_I) + 1
        new_W = new_I + self.real.F
        return ap_complex(new_W, new_I, res, mode=self.mode, overflow=self.overflow)

    def __radd__(self, other) -> 'ap_complex':
        return self.__add__(other)

    def __iadd__(self, other) -> 'ap_complex':
        res = self + other
        self.assign(res.to_complex() if isinstance(res, ap_complex) else res.to_float())
        return self

    def __sub__(self, other) -> 'ap_complex':
        other_val = other.to_complex() if isinstance(other, ap_complex) else (
            other.to_float() if isinstance(other, ap_fixed) else np.asarray(other, dtype=np.complex128))
        res = self.to_complex() - other_val

        if self.PRESERVE_LHS_PRECISION:
            return ap_complex(template=self, val=res)

        other_I = getattr(other, 'I', self.I)
        new_I = max(self.I, other_I) + 1
        new_W = new_I + self.real.F
        return ap_complex(new_W, new_I, res, mode=self.mode, overflow=self.overflow)

    def __rsub__(self, other) -> 'ap_complex':
        other_val = other.to_complex() if isinstance(other, ap_complex) else (
            other.to_float() if isinstance(other, ap_fixed) else np.asarray(other, dtype=np.complex128))
        res = other_val - self.to_complex()

        if self.PRESERVE_LHS_PRECISION:
            return ap_complex(template=self, val=res)

        other_I = getattr(other, 'I', self.I)
        new_I = max(self.I, other_I) + 1
        new_W = new_I + self.real.F
        return ap_complex(new_W, new_I, res, mode=self.mode, overflow=self.overflow)

    def __isub__(self, other) -> 'ap_complex':
        res = self - other
        self.assign(res.to_complex() if isinstance(res, ap_complex) else res.to_float())
        return self

    def __mul__(self, other) -> 'ap_complex':
        other_val = other.to_complex() if isinstance(other, ap_complex) else (
            other.to_float() if isinstance(other, ap_fixed) else np.asarray(other))
        res = self.to_complex() * other_val

        if self.PRESERVE_LHS_PRECISION:
            return ap_complex(template=self, val=res)

        other_W = getattr(other, 'W', self.W)
        other_I = getattr(other, 'I', self.I)
        new_W = self.W + other_W + 1
        new_I = self.I + other_I + 1
        return ap_complex(new_W, new_I, res, mode=self.mode, overflow=self.overflow)

    def __rmul__(self, other) -> 'ap_complex':
        return self.__mul__(other)

    def __imul__(self, other) -> 'ap_complex':
        res = self * other
        self.assign(res.to_complex() if isinstance(res, ap_complex) else res.to_float())
        return self

    def __matmul__(self, other) -> 'ap_complex':
        other_val = other.to_complex() if isinstance(other, ap_complex) else (
            other.to_float() if isinstance(other, ap_fixed) else np.asarray(other))
        res = self.to_complex() @ other_val

        if self.PRESERVE_LHS_PRECISION:
            return ap_complex(template=self, val=res)

        other_W = getattr(other, 'W', self.W)
        other_I = getattr(other, 'I', self.I)
        K = self.to_complex().shape[-1] if len(self.to_complex().shape) > 0 else 1
        accum_bits = (int(np.ceil(np.log2(K))) if K > 1 else 0) + 1
        new_I = self.I + other_I + accum_bits
        new_W = self.W + other_W + accum_bits
        return ap_complex(new_W, new_I, res, mode=self.mode, overflow=self.overflow)

    def __rmatmul__(self, other) -> 'ap_complex':
        other_obj = ap_complex(template=self, val=other)
        return other_obj @ self

    def __imatmul__(self, other) -> 'ap_complex':
        res = self @ other
        self.assign(res.to_complex() if isinstance(res, ap_complex) else res.to_float())
        return self

    def __truediv__(self, other):
        if isinstance(other, ap_complex):
            other_val = other.to_complex()
        elif isinstance(other, ap_fixed):
            other_val = other.to_float()
        else:
            other_val = np.asarray(other)

        res = self.to_complex() / other_val

        if self.PRESERVE_LHS_PRECISION:
            if np.iscomplexobj(res):
                return ap_complex(template=self, val=res)
            return ap_fixed(self.W, self.I, res, mode=self.mode, overflow=self.overflow)

        if np.iscomplexobj(res):
            return ap_complex(template=self, val=res)
        return ap_fixed(self.W, self.I, res, mode=self.mode, overflow=self.overflow)

    def __rtruediv__(self, other):
        other_obj = ap_complex(template=self, val=other)
        return other_obj / self

    def __itruediv__(self, other) -> 'ap_complex':
        res = self / other
        self.assign(res.to_complex() if isinstance(res, ap_complex) else res.to_float())
        return self

    def __neg__(self) -> 'ap_complex':
        return ap_complex(template=self, val=-self.to_complex())

    def __pos__(self) -> 'ap_complex':
        return self

    def __repr__(self):
        return f"ap_complex<{self.W},{self.I},{self.mode},{self.overflow}>\n{self.to_complex()}"

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        if method != '__call__':
            return NotImplemented

        raw_args = tuple(
            x.to_complex() if isinstance(x, ap_complex) else
            (x.to_float() if isinstance(x, ap_fixed) else x)
            for x in inputs
        )

        result = ufunc(*raw_args, **kwargs)

        if isinstance(result, np.ndarray):
            if np.iscomplexobj(result):
                return ap_complex(template=self, val=result)
            else:
                return ap_fixed(self.W, self.I, val=result, mode=self.mode, overflow=self.overflow)
        return result

    def __array_function__(self, func, types, args, kwargs):
        if func in HANDLED_FUNCTIONS:
            return HANDLED_FUNCTIONS[func](*args, **kwargs)

        raw_args = tuple(
            a.to_complex() if isinstance(a, ap_complex) else
            (a.to_float() if isinstance(a, ap_fixed) else a)
            for a in args
        )
        res = func(*raw_args, **kwargs)

        if isinstance(res, np.ndarray):
            if np.iscomplexobj(res):
                return ap_complex(template=self, val=res)
            return ap_fixed(self.W, self.I, val=res, mode=self.mode, overflow=self.overflow)
        return res


@implements(np.real)
def real_override(x):
    if isinstance(x, ap_complex):
        return x.real
    return np.real(x)

@implements(np.imag)
def imag_override(x):
    if isinstance(x, ap_complex):
        return x.imag
    return np.imag(x)

@implements(np.vdot)
def vdot_override(a, b):
    a_cplx = a if isinstance(a, ap_complex) else ap_complex(val=a)
    b_cplx = b if isinstance(b, ap_complex) else ap_complex(val=b)
    return np.sum(a_cplx.conj() * b_cplx)

@implements(np.sum)
def sum_override(a, axis=None, dtype=None, out=None, keepdims=False):
    val = np.sum(a.to_complex() if isinstance(a, ap_complex) else a, axis=axis, keepdims=keepdims)
    if np.iscomplexobj(val):
        return ap_complex(template=a if isinstance(a, ap_complex) else None, val=val)
    return ap_fixed(template=a if isinstance(a, ap_fixed) else None, val=val)

@implements(np.reshape)
def reshape_override(a, newshape, order='C'):
    if hasattr(a, 'reshape'):
        return a.reshape(newshape, order=order)
    return np.reshape(a, newshape, order=order)