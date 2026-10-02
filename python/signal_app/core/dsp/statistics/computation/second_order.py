from .moments import *
import numpy as np

def covariance(x: np.ndarray, y:np.ndarray) -> tuple[complex, np.ndarray]:
    return cross_complex_moment(x=x,y=y,px=1,qx=0,py=0,qy=1, central=True)

def correlation(x: np.ndarray, y:np.ndarray) -> tuple[complex, np.ndarray]:
    return cross_complex_moment(x=x,y=y,px=1,qx=0,py=0,qy=1,central=False)

def variance(x: np.ndarray) -> tuple[complex, np.ndarray]:
    return covariance(x,x)


def autocorrelation(x: np.ndarray) -> tuple[complex, np.ndarray]:
    return correlation(x,x)

def covariance_matrix(X: np.ndarray) -> np.ndarray:
    """ returns an NxN covariance matrix based on X being a NxL multivariate signal matrix"""
    N,L = X.shape
    R = (1/L) * X @ X.conj().T
    return R
