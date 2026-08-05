import numpy as np


class Beamformer:
    def __init__(self):
        pass

    @staticmethod
    def mvdr(X, v_look):
        """Minimum variance distortionless response (MVDR) beamformer
        Uses LCMV with one constraint"""
        f_look = np.ones((1,1)) # distortionless contraint
        Y, w = Beamformer.lcmv(X=X, C=v_look, f=f_look)
        return Y, w

    @staticmethod
    def capon(X, v_look):
        Y, w = Beamformer.frost(X=X, C=v_look, f=np.ones((1,1)))
        return Y, w

    @staticmethod
    def frost(X: np.ndarray, C: np.ndarray, f :np.ndarray, mu:float=0.1, method:str = "newton"):
        """ An LMS based LCMV (Frost) beamformer:
        [1] An Algorithm For Linearly Constrained Adaptive Array Processing, section II"""


        N, L = X.shape
        M = C.shape[0]
        W = np.zeros((N, L+1), dtype=np.complex128)

        # fixed by constrains defined "outside" algorithm loop
        F = C @ np.linalg.pinv(C.conj().T@C) @ f
        W[:,0] = np.squeeze(F)
        P = np.eye(M) - C @ np.linalg.pinv(C.conj().T@C) @ C.conj().T

        # Newtons method, assume R_xx is known
        R_xx = (1/L) * (X @ X.conj().T)
        lambda_max = np.max(np.linalg.eigvals(R_xx).real)
        y = np.zeros((1,L), dtype=np.complex128)
        for i in range(L):
            w = W[:,i:i+1]
            X_k = X[:,i:i+1]
            y[0,i] = np.squeeze(w.conj().T @ X_k)

            match method:
                case "newton":
                    # newton's method
                    w_new = P @ (w - mu/lambda_max * R_xx @ w) + F
                case "iterative":
                    # iterative
                    norm = (X_k.conj().T @X_k)[0,0]
                    mu_n = mu/(1e-12+norm)
                    w_new = P @ (w - mu_n * y[0, i].conj() * X_k) + F
            W[:,i+1:i+2] = w_new

        return y, W[:,L-1]

    @staticmethod
    def lcmv(X: np.ndarray, C: np.ndarray, f :np.ndarray):
        """A matrix based LCMV beamformer:
        X: NxL array data matrix

        [1] An Algorithm For Linearly Constrained Adaptive Array Processing, section II
        [2] Optimum Array Processing, section 6.7"""
        N, L = X.shape

        # from van trees:
        g = f
        S = X @ X.conj().T
        S_inv = np.linalg.pinv(S)
        guts = np.linalg.pinv(C.conj().T @ S_inv @ C)

        print(f"g shape: {np.shape(g)}")
        print(f"C shape: {np.shape(C)}")
        print(f"S shape: {np.shape(S)}")
        print(f"guts shape: {np.shape(guts)}")
        w_conj_lcmv = g.conj().T @ guts @ C.conj().T @ S_inv

        print(f"w_conj_lcmv shape: {np.shape(w_conj_lcmv)}")

        Y = w_conj_lcmv @ X
        w = w_conj_lcmv[:,-1]

        return Y, w.conj().T


    @staticmethod
    def get_window(N: int, window: str="Bartlett"):
        match window:
            case "Bartlett":
                return np.ones(N)
            case "Welch":
                return np.hanning(N)
            case _:
                raise ValueError("Invalid window function")
