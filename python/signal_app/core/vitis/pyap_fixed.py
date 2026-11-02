import numpy as np
from fxpmath import Fxp

DEFAULT_MARKER = object()


class ap_fixed:
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
        # Preserve original unquantized source data for fluid .typedef() chaining
        self._orig_val = val_data
        self._update_val(val_data)

    @staticmethod
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

        fxp_round = self.QUANT_MAP.get(self.mode, 'bit_trunc')
        fxp_overflow = self.OVERFLOW_MAP.get(self.overflow, 'wrap')

        # Handle Standard vs Custom Overflow Modes
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
            # First quantize using standard Fxp without clipping
            temp_fxp = Fxp(val=val_arr, signed=True, n_word=self.W, n_frac=self.F, overflow='wrap', rounding=fxp_round)
            quantized_val = temp_fxp.get_val()

            # Dynamic bounds
            max_val = (2 ** (self.I - 1)) - (2 ** (-self.F))
            min_val = -(2 ** (self.I - 1))

            if self.overflow == 'AP_SAT_ZERO':
                # Force to 0.0 on overflow or underflow
                mask_overflow = (quantized_val > max_val) | (quantized_val < min_val)
                quantized_val = np.where(mask_overflow, 0.0, quantized_val)

            elif self.overflow == 'AP_SAT_SYM':
                # Symmetrical saturation: clip to [-MAX, +MAX]
                sym_min = -max_val
                quantized_val = np.clip(quantized_val, sym_min, max_val)

            elif self.overflow == 'AP_WRAP_SM':
                # Sign-magnitude wraparound
                sign = np.sign(quantized_val)
                abs_val = np.abs(quantized_val)
                scale = 2 ** self.F
                raw_mag = np.floor(abs_val * scale).astype(np.int64)
                modulus = 1 << (self.W - 1)
                wrapped_mag = raw_mag % modulus
                quantized_val = sign * (wrapped_mag / scale)

            self._fxp = Fxp(val=quantized_val, signed=True, n_word=self.W, n_frac=self.F, overflow='wrap',
                            rounding='bit_trunc')

    def assign(self, val) -> 'ap_fixed':
        self._orig_val = val
        self._update_val(val)
        return self

    def __ilshift__(self, other) -> 'ap_fixed':
        self._orig_val = other
        self._update_val(other)
        return self

    def typedef(self, type_template) -> 'ap_fixed':
        """Fluid method: ap_fixed(matrix).typedef(a_t)"""
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
        return self._fxp.get_val()

    def raw(self) -> np.ndarray:
        return self._fxp.raw()

    @property
    def shape(self):
        return self._fxp.val.shape if isinstance(self._fxp.val, np.ndarray) else ()

    # --- Matrix Multiplication (@) ---
    def __matmul__(self, other) -> 'ap_fixed':
        if not isinstance(other, ap_fixed):
            other = ap_fixed(self.W, self.I, other, self.mode, self.overflow)

        K = self.shape[-1] if len(self.shape) > 0 else 1
        accum_bits = int(np.ceil(np.log2(K))) if K > 1 else 0

        new_I = self.I + other.I + accum_bits
        new_W = self.W + other.W + accum_bits

        res_float = self.to_float() @ other.to_float()
        return ap_fixed(new_W, new_I, res_float, mode=self.mode, overflow=self.overflow)

    def __rmatmul__(self, other) -> 'ap_fixed':
        other_obj = ap_fixed(self.W, self.I, other, self.mode, self.overflow)
        return other_obj @ self

    # --- Elementwise Arithmetic ---
    def __add__(self, other) -> 'ap_fixed':
        other_obj = other if isinstance(other, ap_fixed) else ap_fixed(self.W, self.I, other, self.mode, self.overflow)
        new_I = max(self.I, other_obj.I) + 1
        new_F = max(self.F, other_obj.F)
        new_W = new_I + new_F
        return ap_fixed(new_W, new_I, self.to_float() + other_obj.to_float(), mode=self.mode, overflow=self.overflow)

    def __radd__(self, other) -> 'ap_fixed':
        return self.__add__(other)

    def __sub__(self, other) -> 'ap_fixed':
        other_obj = other if isinstance(other, ap_fixed) else ap_fixed(self.W, self.I, other, self.mode, self.overflow)
        new_I = max(self.I, other_obj.I) + 1
        new_F = max(self.F, other_obj.F)
        new_W = new_I + new_F
        return ap_fixed(new_W, new_I, self.to_float() - other_obj.to_float(), mode=self.mode, overflow=self.overflow)

    def __rsub__(self, other) -> 'ap_fixed':
        other_obj = ap_fixed(self.W, self.I, other, self.mode, self.overflow)
        return other_obj - self

    def __mul__(self, other) -> 'ap_fixed':
        other_obj = other if isinstance(other, ap_fixed) else ap_fixed(self.W, self.I, other, self.mode, self.overflow)
        new_W = self.W + other_obj.W
        new_I = self.I + other_obj.I
        return ap_fixed(new_W, new_I, self.to_float() * other_obj.to_float(), mode=self.mode, overflow=self.overflow)

    def __rmul__(self, other) -> 'ap_fixed':
        return self.__mul__(other)

    def __repr__(self):
        return f"ap_fixed<{self.W},{self.I},{self.mode},{self.overflow}>\n{self.to_float()}"


class ap_complex:
    def __init__(self, W=16, I=4, val=DEFAULT_MARKER, mode='AP_TRN', overflow='AP_WRAP', template=None):
        self.W, self.I, val_data, self.mode, self.overflow = ap_fixed._parse_args(
            W, I, val, mode, overflow, template
        )
        val_arr = np.zeros((), dtype=np.complex128) if val_data is DEFAULT_MARKER else np.asarray(val_data, dtype=np.complex128)
        self._orig_val = val_data

        self.real = ap_fixed(self.W, self.I, val_arr.real, mode=self.mode, overflow=self.overflow)
        self.imag = ap_fixed(self.W, self.I, val_arr.imag, mode=self.mode, overflow=self.overflow)

    def to_complex(self) -> np.ndarray:
        return self.real.to_float() + 1j * self.imag.to_float()

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

    @property
    def shape(self):
        return self.real.shape

    # --- Complex Matrix Multiplication (@) ---
    def __matmul__(self, other) -> 'ap_complex':
        if not isinstance(other, ap_complex):
            other = ap_complex(self.W, self.I, other, self.mode, self.overflow)

        K = self.shape[-1] if len(self.shape) > 0 else 1
        accum_bits = (int(np.ceil(np.log2(K))) if K > 1 else 0) + 1

        new_I = self.I + other.I + accum_bits
        new_W = self.W + other.W + accum_bits

        res_complex = self.to_complex() @ other.to_complex()
        return ap_complex(new_W, new_I, res_complex, mode=self.mode, overflow=self.overflow)

    def __rmatmul__(self, other) -> 'ap_complex':
        other_obj = ap_complex(self.W, self.I, other, self.mode, self.overflow)
        return other_obj @ self

    # --- Elementwise Arithmetic ---
    def __add__(self, other) -> 'ap_complex':
        other_obj = other if isinstance(other, ap_complex) else ap_complex(self.W, self.I, other, self.mode, self.overflow)
        new_I = max(self.I, other_obj.I) + 1
        new_F = max(self.real.F, other_obj.real.F)
        new_W = new_I + new_F
        return ap_complex(new_W, new_I, self.to_complex() + other_obj.to_complex(), mode=self.mode, overflow=self.overflow)

    def __radd__(self, other) -> 'ap_complex':
        return self.__add__(other)

    def __sub__(self, other) -> 'ap_complex':
        other_obj = other if isinstance(other, ap_complex) else ap_complex(self.W, self.I, other, self.mode, self.overflow)
        new_I = max(self.I, other_obj.I) + 1
        new_F = max(self.real.F, other_obj.real.F)
        new_W = new_I + new_F
        return ap_complex(new_W, new_I, self.to_complex() - other_obj.to_complex(), mode=self.mode, overflow=self.overflow)

    def __rsub__(self, other) -> 'ap_complex':
        other_obj = ap_complex(self.W, self.I, other, self.mode, self.overflow)
        return other_obj - self

    def __mul__(self, other) -> 'ap_complex':
        other_obj = other if isinstance(other, ap_complex) else ap_complex(self.W, self.I, other, self.mode, self.overflow)
        new_W = self.W + other_obj.W + 1
        new_I = self.I + other_obj.I + 1
        return ap_complex(new_W, new_I, self.to_complex() * other_obj.to_complex(), mode=self.mode, overflow=self.overflow)

    def __rmul__(self, other) -> 'ap_complex':
        return self.__mul__(other)

    def __repr__(self):
        return f"ap_complex<{self.W},{self.I},{self.mode},{self.overflow}>\n{self.to_complex()}"