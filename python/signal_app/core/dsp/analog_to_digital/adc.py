from dataclasses import dataclass
import copy
from typing import List, Union
import numpy as np


@dataclass
class ADC:
    """Multichannel ADC supporting duck-typed Signal lists or raw Data Matrices.

    Parameters
    ----------
    ktb_db_int16 : float
        Target thermal noise (kTB) floor in dB relative to 1 LSB^2 power.
        Default = 10.0 dB (variance = 10 LSB^2).
    bits : int
        ADC bit resolution (default 16 bits -> [-32768, +32767]).
    saturate : bool
        If True, clips overflowing signals at rail bounds. If False, wraps around.
    add_dither : bool
        If True, adds +/- 0.5 LSB uniform dither prior to rounding.
    return_complex_dtype : bool
        If True, returns complex128 with integer values (e.g. 1024.0 + 512.0j)
        to maintain total matrix compatibility with downstream DSP blocks.
    """

    ktb_db_int16: float = 10.0
    bits: int = 16
    saturate: bool = True
    add_dither: bool = False
    return_complex_dtype: bool = True

    def __post_init__(self):
        self.max_int = (1 << (self.bits - 1)) - 1  # +32767 for 16-bit
        self.min_int = -(1 << (self.bits - 1))  # -32768 for 16-bit
        self.X_dig: np.ndarray = None
        self.last_clip_count: int = 0
        self.last_total_samples: int = 0

    def process(
        self, signals: Union[list, np.ndarray], ktb_var: float
    ) -> Union[list, np.ndarray]:
        """Digitizes input signals or data matrix.

        Parameters
        ----------
        signals : list or np.ndarray
            Either a list of Signal instances (with .iq attributes) or a raw data matrix (M, L).
        ktb_var : float
            Thermal noise variance of the incoming floating-point data.
        """
        if ktb_var <= 0:
            raise ValueError("ktb_var must be strictly positive.")

        # Duck-typing check matching antenna receive pattern
        is_signal_list = (
            isinstance(signals, list)
            and len(signals) > 0
            and hasattr(signals[0], "iq")
            and hasattr(signals[0], "__class__")
        )

        if is_signal_list:
            # Extract data matrix from Signal list: shape (M, L)
            X_float = np.vstack([sig.iq for sig in signals])

            # Perform core digitization
            self.X_dig = self._digitize_matrix(X_float, ktb_var)

            # Create deep copies of signal objects and update their IQ payload
            dig_sigs = copy.deepcopy(signals)
            for idx, sig in enumerate(dig_sigs):
                sig.iq = (
                    self.X_dig[idx, :] if self.X_dig.ndim > 1 else self.X_dig
                )

            return dig_sigs

        else:
            # Inputs are already a numpy data matrix
            X_float = np.asarray(signals)
            self.X_dig = self._digitize_matrix(X_float, ktb_var)

            return self.X_dig

    def _digitize_matrix(
        self, X_float: np.ndarray, ktb_var_input: float
    ) -> np.ndarray:
        """Core digitization engine mapping floating-point noise floor to target LSB^2."""
        # 1. Target integer kTB power in LSB^2
        target_ktb_power = 10.0 ** (self.ktb_db_int16 / 10.0)

        # 2. Scale factor mapping float noise floor -> int16 LSB^2
        scale_factor = np.sqrt(target_ktb_power / ktb_var_input)

        # 3. Apply gain
        X_scaled = X_float * scale_factor
        I_scaled = X_scaled.real
        Q_scaled = X_scaled.imag

        # 4. Optional dither
        if self.add_dither:
            I_scaled += np.random.uniform(-0.5, 0.5, size=I_scaled.shape)
            Q_scaled += np.random.uniform(-0.5, 0.5, size=Q_scaled.shape)

        # 5. Round to nearest LSB
        I_round = np.round(I_scaled)
        Q_round = np.round(Q_scaled)

        # 6. Rail bounds and clipping
        if self.saturate:
            I_clipped = np.clip(I_round, self.min_int, self.max_int)
            Q_clipped = np.clip(Q_round, self.min_int, self.max_int)

            # Track saturation stats
            clips = np.sum(I_round != I_clipped) + np.sum(Q_round != Q_clipped)
            self.last_clip_count = int(clips)
            self.last_total_samples = I_scaled.size * 2
        else:
            I_clipped = (
                (I_round - self.min_int) % (1 << self.bits)
            ) + self.min_int
            Q_clipped = (
                (Q_round - self.min_int) % (1 << self.bits)
            ) + self.min_int

        # Cast outputs
        I_int = I_clipped.astype(np.int16)
        Q_int = Q_clipped.astype(np.int16)

        if self.return_complex_dtype:
            return I_int.astype(np.complex128) + 1j * Q_int.astype(
                np.complex128
            )
        else:
            return I_int + 1j * Q_int

    @property
    def clip_rate(self) -> float:
        """Percentage of clipped I & Q samples in the last digitization call."""
        if self.last_total_samples == 0:
            return 0.0
        return (self.last_clip_count / self.last_total_samples) * 100.0