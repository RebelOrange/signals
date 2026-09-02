import numpy as np
from dataclasses import dataclass

@dataclass
class Wiener:
    X: np.ndarray
    d: np.ndarray
    order: int = 3
    def __post_init__(self):
        self.M, self.L = self.X.shape
        self.N = self.M*self.order

    def compute_weights(self, X_vectorized:np.ndarray, d:np.ndarray):
        R_xx = (X_vectorized @ X_vectorized.conj().T)/self.L
        r_xd = (X_vectorized @ d.conj().T)/self.L

        w_opt = np.linalg.inv(R_xx)@r_xd

        self.w_opt = w_opt
        self.r_xd = r_xd
        self.R_xx = R_xx

        return w_opt

    def run(self):
        buffer = np.zeros((self.M, self.order), dtype=np.complex128)
        X_vectorized = np.zeros((self.N, self.L), dtype=np.complex128)

        for i in range(self.L):
            buffer[:, 1:] = buffer[:, :-1]
            buffer[:, 0] = self.X[:, i]
            X_vectorized[:,i] = buffer.ravel()

        w_opt = self.compute_weights(X_vectorized, self.d)
        y = w_opt.conj().T@X_vectorized
        e = self.d - y

        return e, y, w_opt




