from typing import Optional

import numpy as np
from dataclasses import dataclass

from .registry import register_provider

@staticmethod
def H(x: np.ndarray):
    return x.conj().T

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

    def kernal(self, X: np.ndarray, d: np.ndarray, mu: float = 0.99, fir_order:int = 3, init_weight: str = "zeros"):
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




