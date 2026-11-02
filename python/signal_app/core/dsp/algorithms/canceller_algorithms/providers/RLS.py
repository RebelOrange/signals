from typing import Optional

import numpy as np
from dataclasses import dataclass
from core.vitis.pyap_fixed import ap_fixed, ap_complex

from .registry import register_provider

def H(A):
    if isinstance(A, ap_complex):
        return np.conj(A.to_complex().T)
    return np.conj(A.T)

@dataclass
class RLS:
    """A multichannel spatial-temporal NLMS algorithm
    X: Auxilary channels
    d: Desired Channel
    mu: learning rate
    order: FIR filter order"""
    X: np.array
    d: np.array
    mu: float = 0.01
    order: int = 3
    gamma: float = 0
    eps: float = np.finfo(float).eps

    def kernal_ap_fixed(
            self,
            X: np.ndarray,
            d: np.ndarray,
            mu: float = 0.99,
            fir_order: int = 3,
            X_t: ap_complex = None,
            W_t: ap_complex = None,
            P_t: ap_complex = None
    ):
        """
        Bit-exact hardware emulation of the RLS Adaptive Filter Kernel using ap_fixed/ap_complex types.
        All data instantiations utilize the fluid `.typedef()` method.
        """
        # ------------------------------------------------------------------
        # 1. Define Hardware Type Archetypes
        # ------------------------------------------------------------------
        if X_t is None:
            X_t = ap_complex(16, 2, mode='AP_TRN', overflow='AP_WRAP')  # Input ADC spec
        if W_t is None:
            W_t = ap_complex(24, 4, mode='AP_TRN', overflow='AP_SAT')  # Filter Weights
        if P_t is None:
            P_t = ap_complex(32, 12, mode='AP_TRN', overflow='AP_SAT')  # Inverse Covariance

        # Real scalar type archetypes
        denom_t = ap_fixed(32, 12, mode='AP_TRN', overflow='AP_SAT')
        mu_t = ap_fixed(16, 2, mode='AP_TRN', overflow='AP_WRAP')

        # Quantize constant mu using .typedef()
        mu_fixed = ap_fixed(mu).typedef(mu_t)

        # Dimensions
        N, L = np.shape(X)
        M = N * fir_order

        # ------------------------------------------------------------------
        # 2. Quantize Input Signals into Hardware Registers
        # ------------------------------------------------------------------
        X_f = ap_complex(X).typedef(X_t)
        d_f = ap_complex(d).typedef(X_t)

        # ------------------------------------------------------------------
        # 3. Estimate Initial Regularization & Covariance Matrix P_0
        # ------------------------------------------------------------------
        sigma_x2 = np.mean(np.abs(X) ** 2)
        c = 0.01
        reg_param = c * sigma_x2 if sigma_x2 > 0 else 0.01

        # Initial Inverse Covariance Matrix P_0
        P0_val = (1.0 / reg_param) * np.eye(M, dtype=np.complex128)
        P = ap_complex(P0_val).typedef(P_t)

        # Preset weight, buffer, and step registers using .typedef()
        W = ap_complex(np.zeros((M, 1), dtype=np.complex128)).typedef(W_t)
        buffer = ap_complex(np.zeros((N, fir_order), dtype=np.complex128)).typedef(X_t)
        U = ap_complex(np.zeros((M, 1), dtype=np.complex128)).typedef(X_t)

        # Temporary internal state variables
        pi = ap_complex(np.zeros((M, 1), dtype=np.complex128)).typedef(P_t)
        k = ap_complex(np.zeros((M, 1), dtype=np.complex128)).typedef(W_t)
        denom = ap_fixed(0.0).typedef(denom_t)

        # Output storage arrays (NumPy arrays of float/complex values)
        e_out = np.zeros(L, dtype=np.complex128)
        y_out = np.zeros(L, dtype=np.complex128)
        W_out = np.zeros((M, L), dtype=np.complex128)

        # ------------------------------------------------------------------
        # 4. RLS Iterative Loop (Hardware Clock Cycle Simulation)
        # ------------------------------------------------------------------
        for i in range(L):
            # 1. Delay Line / FIFO Buffer Shift
            buf_c = buffer.to_complex()
            buf_c[:, 1:] = buf_c[:, :-1]
            buf_c[:, 0] = X_f.to_complex()[:, i]
            buffer <<= buf_c  # Truncates/saturates back to X_t spec

            # 2. Vectorize Buffer into Input Vector U
            U <<= buffer.to_complex().flatten(order="F").reshape(-1, 1)

            # 3. Compute Kalman Gain Vector: pi = P @ U
            pi <<= P @ U  # Matrix product bit-grows, then streams into P_t

            # 4. Compute Real Denominator: denom = mu + Real(U^H @ pi)
            u_pi = H(U) @ pi  # Scalar complex product
            denom_val = mu_fixed.to_float() + u_pi.to_complex().item().real
            denom <<= denom_val  # Casts to 32-bit fixed point

            # 5. Compute Kalman Gain Vector: k = pi / denom
            k_val = pi.to_complex() / denom.to_float()
            k <<= k_val  # Casts to W_t spec

            # 6. Filter Output y[i] and Error e[i] using .typedef()
            y_val = (H(W) @ U).to_complex().item()
            d_val = d_f.to_complex()[i] if d_f.shape != () else d_f.to_complex()

            y_i = ap_complex(y_val).typedef(X_t)
            e_i = ap_complex(d_val - y_i.to_complex()).typedef(X_t)

            # Record output scalars
            y_out[i] = y_i.to_complex()
            e_out[i] = e_i.to_complex()

            # 7. Weight Vector Update: W = W + k * conj(e[i])
            e_conj = np.conj(e_i.to_complex())
            W <<= W + (k * e_conj)  # Accumulates and saturates to W_t spec

            # 8. Inverse Covariance Matrix Update (Woodbury Identity): P = (P - k @ pi^H) / mu
            P_update = (P - (k @ H(pi))) * (1.0 / mu_fixed.to_float())
            P <<= P_update  # Casts and saturates back to P_t spec

            # 9. Record Weight History Snapshot
            W_out[:, i] = W.to_complex().squeeze()

        return e_out, y_out, W_out

    def kernal(self, X: np.ndarray, d: np.ndarray, mu: float = 0.99, fir_order:int = 3):
        # input dimensions of X
        N, L = np.shape(X)
        M = N*fir_order

        # initialize matrices
        e = np.zeros(L, dtype=np.complex128)
        y = np.zeros(L,dtype=np.complex128)

        W = np.zeros((M, 1), dtype=np.complex128)
        W_out = np.zeros((M, L), dtype=np.complex128)

        buffer = np.zeros((N, fir_order), dtype=np.complex128)
        U = np.zeros((M, 1), dtype=np.complex128)

        # Estimate input signal variance/power across all channels and snapshots
        sigma_x2 = np.mean(np.abs(X) ** 2)

        # Scale reg_param proportional to input power (c = 0.01 for moderate/high SNR)
        c = 0.01
        reg_param = c * sigma_x2 if sigma_x2 > 0 else 0.01

        P = np.zeros((M, M), dtype=np.complex128)
        P[:,:] = (1/reg_param) * np.eye(M, dtype=np.complex128)

        # For loop
        for i in range(0,L):

            # fifo buffer
            buffer[:, 1:] = buffer[:, :-1]
            buffer[:, 0] = X[:, i]

            # vectorize buffer
            U = buffer.flatten(order="F").reshape(-1,1)

            pi = P @ U  # Shape: (M, 1)
            denom = mu + (H(U) @ pi).item().real  # Complex scalar
            k = pi / denom  # Shape: (M, 1)

            # 4. Filter output and a priori estimation error
            y[i] = (H(W) @ U).item()  # Complex scalar
            e[i] = d[i] - y[i]  # Complex scalar

            # 5. Weight vector update
            W += k * np.conj(e[i])

            # 6. Inverse covariance matrix update (Woodbury identity)
            P = (P - k @ H(pi)) / mu

            # 7. Record current updated weights
            W_out[:, i] = W.squeeze()

        return e, y, W_out

    def run(self):
        return self.kernal(self.X, self.d, self.mu, self.order)

@dataclass
class RLSConfig:
    mu: float = 0.9
    order: int = 3

@register_provider(RLSConfig)
class RLSProvider:
    def __init__(self, config: RLSConfig):
        self._config = config

    def process_datamatrix(self, X: np.ndarray) -> np.ndarray:
        # assumes first channel in data matrix is the desired channel
        pass




