from typing import Optional

import numpy as np
from dataclasses import dataclass

from .registry import register_provider

@staticmethod
def mvdr(X:np.array, v_look:np.array):
    M, L = X.shape
    R_xx = (1/L)*(X@X.conj().T)
    R_inv = np.linalg.pinv(R_xx)
    num = v_look.conj().T @R_inv
    dem = v_look.conj().T @ R_inv @ v_look
    w_conj = dem @ num
    w = w_conj.conj().T
    return w

@dataclass
class MvdrConfig:
    pass

@register_provider(MvdrConfig)
class MvdrProvider:
    def __init__(self, config: MvdrConfig):
        self._config = config

    def process_datamatrix(self, X, v_steer) -> np.ndarray:
        w = mvdr(X, v_steer)

        return w.conj().T@X

    def calculate_weights(self, X, v_steer, f_constraint) -> np.ndarray:
        return mvdr(X, v_steer)
