from typing import Optional

import numpy as np
from dataclasses import dataclass
from core.vitis.pyap_fixed import ap_fixed, ap_complex

from core.dsp.algorithms.canceller_algorithms.providers.registry import register_provider

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
    mu: float = 0.01
    order: int = 3
    eps: float = np.finfo(float).eps

    def run_ap_fixed(self, X_in: np.ndarray, d_in: np.ndarray):

        mu = self.mu
        fir_order = self.order
        eps = self.eps

        ### ap_fixed typing ###
        int16_t = ap_fixed(14,2, mode="AP_RND_CONV", overflow="AP_SAT")
        sc16_t = ap_complex(template=int16_t)

        # weight vector bits
        w_frac_bits = 26; w_int_bits = 6
        weight_t = ap_fixed(w_frac_bits+w_int_bits,w_int_bits, mode="AP_RND_CONV")
        weight_cplx = ap_complex(template=weight_t)

        # P inverse covariance matrix
        P_frac_bits = 24; P_int_bits = 8
        P_mat_t = ap_fixed(P_frac_bits+P_int_bits,P_int_bits, mode="AP_RND_CONV")
        P_mat_cplx = ap_complex(template=P_mat_t)

        # forgetting factor mu
        mu_t = ap_fixed(8, 2, mode="AP_RND_CONV")
        #mu = ap_fixed(mu).typedef(mu_t)

        # error
        e_frac_bits = 20; e_int_bits = 4
        error_t = ap_fixed(e_frac_bits+e_int_bits, e_int_bits, mode="AP_RND_CONV")
        error_cplx = ap_complex(template=error_t)


        # normalize input
        X = ap_complex(X_in / 2 ** 14).typedef(sc16_t)
        d = ap_complex(d_in / 2 ** 14).typedef(sc16_t)

        # input dimensions of X
        N, L = np.shape(X)
        M = N*fir_order


        # initialize matrices
        e = ap_complex(np.zeros(L, dtype=np.complex128)).typedef(error_cplx)
        y = ap_complex(np.zeros(L,dtype=np.complex128)).typedef(error_cplx)

        W = ap_complex(np.zeros((M, 1), dtype=np.complex128)).typedef(weight_cplx)
        W_out = ap_complex(np.zeros((M, L), dtype=np.complex128)).typedef(weight_cplx)

        buffer = ap_complex(np.zeros((N, fir_order), dtype=np.complex128)).typedef(sc16_t)
        U = ap_complex(np.zeros((M, 1), dtype=np.complex128)).typedef(sc16_t)

        # Estimate input signal variance/power across all channels and snapshots
        sigma_x2 = np.mean(np.abs(X.to_complex()) ** 2)

        # Scale reg_param proportional to input power (c = 0.01 for moderate/high SNR)
        c = 0.01
        reg_param = c * sigma_x2 if sigma_x2 > 0 else 0.01

        P = ap_complex(np.zeros((M, M), dtype=np.complex128)).typedef(P_mat_cplx)
        P[:,:] = ap_complex((10) * np.eye(M, dtype=np.complex128)).typedef(P_mat_cplx)

        # For loop
        for i in range(0,L):

            # fifo buffer
            buffer[:, 1:] = buffer[:, :-1]
            buffer[:, 0] = ap_complex(X[:, i]).typedef(sc16_t)

            # vectorize buffer
            U = buffer.flatten(order="F").reshape(-1,1)

            pi = P @ U  # Shape: (M, 1)
            denom = mu + (H(U) @ pi).item().real
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

        return e.to_complex(), y.to_complex(), W_out.to_complex()

    def run(self, X: np.ndarray, d: np.ndarray):
        mu = self.mu
        fir_order = self.order
        eps = self.eps

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


@dataclass
class RLSConfig:
    mu: float = 0.9
    order: int = 3
    eps: float = 2**(-32)

@register_provider(RLSConfig)
class RLSProvider:
    def __init__(self, config: RLSConfig):
        self._config = config

    def run(self, X: np.ndarray, d: np.ndarray, mu: float = 0.99, order: int = 3, precision: str = "float"):
        proc = RLS(mu=self._config.mu, order=self._config.order, eps=self._config.eps)
        if precision == "float":
            e, y, W_out = proc.run(X=X, d=d, mu=self._config.mu, fir_order=self._config.order)
        elif precision == "ap_fixed":
            e, y, W = proc.run_ap_fixed(X_in=X, d_in=d)
        return e, y, W_out

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    # AP fixed types from vitis
    int16_t_zero = ap_fixed(16, 16, mode="AP_RND_ZERO", overflow="AP_SAT")
    int16_t_conv = ap_fixed(16, 16, mode="AP_RND_CONV", overflow="AP_SAT")

    # random data
    N = 8096
    x = (100.0 * (np.random.normal(size=N) + 1j * np.random.normal(size=N)))[np.newaxis, :]
    x_shift = 3 * np.exp(1j * 0.55 * np.pi) * x + 10*np.random.normal(size=N) + 1j * np.random.normal(size=N)
    x_shift_2 = 6 * np.exp(1j * -0.75 * np.pi) * x +10*np.random.normal(size=N) + 1j * np.random.normal(size=N)

    X = np.vstack((x_shift, x_shift_2))
    R = X @ X.conj().T
    np.linalg.matrix_rank(R)
    print(f"R:")
    print(R)
    print(f"rank: {np.linalg.matrix_rank(R)}")
    print(np.shape(x))
    print(np.shape(X))

    # print(x)
    # print(np.round(x))

    rls = RLS(mu=0.999, order=1)

    e, y, W = rls.run_ap_fixed(X_in=X, d_in=x[0, :])
    e = e*2**14
    print(f"error mean: {np.mean(np.real(e))} (real), {np.mean(np.imag(e))} (imag)")

    plt.figure()
    plt.plot(np.real(x[0,:]),"b-")
    plt.plot(np.imag(x[0,:]),"r-")
    plt.plot(np.real(e),"b--")
    plt.plot(np.imag(e),"r--")
    ylim = np.max(np.abs(x))
    plt.ylim((-ylim, ylim))

    plt.figure()
    plt.plot(np.real(W[0, :]), "b-")
    plt.plot(np.imag(W[0, :]), "r-")
    plt.plot(np.real(W[1, :]), "b--")
    plt.plot(np.imag(W[1, :]), "r--")

    print(np.mean(np.real(W[0, 200:])))

    plt.show()
    pass





