from typing import Optional

import numpy as np
from dataclasses import dataclass

from core.vitis.pyap_fixed import ap_fixed, ap_complex
from .registry import register_provider

@staticmethod
def H(x: np.ndarray):
    return x.conj().T

@dataclass
class nlms:
    mu: float = 0.01
    order: int = 3
    gamma: float = 0
    eps: float = np.finfo(float).eps

    def run_ap_fixed(self, X_in, d_in):
        # datatypes from vitis
        fractional_bits = 12
        int16_t = ap_fixed(16,16, mode="AP_RND_CONV", overflow="AP_SAT")
        sc16_t = ap_complex(template=int16_t)
        weight_t = ap_fixed(64-32+fractional_bits,32, mode="AP_RND_CONV")
        weight_cplx = ap_complex(template=weight_t)
        error_t = ap_fixed(64-32+fractional_bits,32, mode="AP_RND_CONV")
        error_cplx = ap_complex(template=error_t)
        mu_t = ap_fixed(64-32+fractional_bits,32, mode="AP_RND_CONV")
        inner_prod = ap_fixed(64-32+fractional_bits, 32)

        X = ap_complex(X_in).typedef(sc16_t)
        d = ap_complex(d_in).typedef(sc16_t)
        mu = ap_fixed(self.mu).typedef(mu_t)
        eps = ap_fixed(2**(-fractional_bits+1)).typedef(error_t)
        print(eps.to_float())
        gamma = 0

        M, L = np.shape(X)  # number of channels, length of signal vector
        y = ap_complex(np.zeros(L, dtype=np.complex128)).typedef(error_cplx)
        e = ap_complex(np.zeros(L, dtype=np.complex128)).typedef(error_cplx)

        buffer = ap_complex(np.zeros((M, self.order), dtype=np.complex128)).typedef(sc16_t)
        W = ap_complex(np.zeros((M * self.order, L), dtype=np.complex128)).typedef(weight_cplx)
        w = ap_complex(np.zeros(M * self.order, dtype=np.complex128)).typedef(weight_cplx)

        for i in range(L):
            # FIFO buffer
            buffer[:, 1:] = buffer[:, :-1]

            # Insert the new column at the very beginning
            buffer[:, 0] = X[:, i]

            # get previous weights
            w = W[:, i]

            # Vectorize
            x_fifo = buffer.flatten(order="F")  # shape (M*order,)
            y[i] = H(w) @ x_fifo
            e[i] = d[i] - y[i]

            # step weights
            mu_norm = mu / (np.vdot(x_fifo, x_fifo).real + eps)
            w = (1.0 - mu_norm * gamma) * w + mu_norm * e[i].conj() * x_fifo
            if i % 100 == 0:
                for m in range(M):
                    continue
                    N = 1
                    desired_variance = 0.000 * np.abs(w[m])  # e.g., variance = 4 (std dev = 2)
                    sigma = np.sqrt(desired_variance)
                    v_real = np.random.normal(loc=0.0, scale=sigma, size=(N, 1))
                    v_imag = np.random.normal(loc=0.0, scale=sigma, size=(N, 1))
                    w[m] += v_real + 1j * v_imag
            if i == L - 1:
                break
            W[:, i + 1] = w

        return e.to_complex(), y.to_complex(), W.to_complex()


    def run(self, X: np.ndarray, d: np.ndarray):
        M, L = np.shape(X) # number of channels, length of signal vector
        y = np.zeros(L, dtype=np.complex128)
        e = np.zeros(L, dtype=np.complex128)
        buffer = np.zeros((M, self.order), dtype=np.complex128)
        W = np.zeros((M*self.order, L), dtype=np.complex128)
        w = np.zeros(M*self.order, dtype=np.complex128)

        for i in range(L):
            # FIFO buffer
            buffer[:, 1:] = buffer[:, :-1]

            # Insert the new column at the very beginning
            buffer[:, 0] = X[:, i]

            # get previous weights
            w = W[:,i]

            # Vectorize
            x_fifo = buffer.flatten(order="F") # shape (M*order,)
            y[i] = H(w) @ x_fifo
            e[i] = d[i]-y[i]

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
    # lms family of algorithms hyper parameters
    mu: float = 0.1
    gamma: float = 0.0 # leaky lms only
    order: int = 3
    eps: float = 2**(-32) # standard floating point precision


@register_provider(LmsConfig)
class LmsProvider:
    def __init__(self, config: LmsConfig):
        self._config = config

    def run(self, X: np.ndarray, d: np.ndarray, precision: str = "float"):
        proc = nlms(mu=self._config.mu, gamma=self._config.gamma, order=self._config.order, eps=self._config.eps)
        if precision == "float":
            e, y, W = proc.run(X=X, d=d)
        elif precision == "ap_fixed":
            e, y, W = proc.run_ap_fixed(X_in=X, d_in=d)
        return e, y, W




