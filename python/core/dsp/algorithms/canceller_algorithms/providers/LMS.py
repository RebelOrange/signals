from typing import Optional

import numpy as np
from dataclasses import dataclass

from .registry import register_provider

@staticmethod
def H(x: np.ndarray):
    return x.conj().T

@dataclass
class nlms:
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


    def run(self):
        M, L = np.shape(self.X) # number of channels, length of signal vector
        y = np.zeros(L, dtype=np.complex128)
        e = np.zeros(L, dtype=np.complex128)
        buffer = np.zeros((M, self.order), dtype=np.complex128)
        W = np.zeros((M*self.order, L), dtype=np.complex128)
        w = np.zeros(M*self.order, dtype=np.complex128)

        for i in range(L):
            # FIFO buffer
            buffer[:, 1:] = buffer[:, :-1]

            # Insert the new column at the very beginning
            buffer[:, 0] = self.X[:, i]

            # get previous weights
            w = W[:,i]

            # Vectorize
            x_fifo = buffer.flatten() # shape (M*order,)
            y[i] = H(w) @ x_fifo
            e[i] = self.d[i]-y[i]

            # step weights
            mu_norm = self.mu/(np.vdot(x_fifo, x_fifo).real+self.eps)
            w = (1.0-mu_norm*self.gamma)*w +mu_norm * e[i].conj()* x_fifo
            if i % 100 ==0:
                for m in range(M):
                    N = 1
                    desired_variance = 0.000*np.abs(w[m])  # e.g., variance = 4 (std dev = 2)
                    sigma = np.sqrt(desired_variance)
                    v_real = np.random.normal(loc=0.0, scale=sigma, size=(N, 1))
                    v_imag = np.random.normal(loc=0.0, scale=sigma, size=(N, 1))
                    w[m]+=v_real+1j*v_imag
            if i == L-1:
                break
            W[:, i+1] = w

        return e, y, W

@dataclass
class LmsConfig:
    mu: float = 0.01
    order: int = 3

@register_provider(LmsConfig)
class LmsProvider:
    def __init__(self, config: LmsConfig):
        self._config = config

    def process_datamatrix(self, X: np.ndarray) -> np.ndarray:
        # assumes first channel in data matrix is the desired channel
        pass




