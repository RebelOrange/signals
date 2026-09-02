import numpy as np
from .moments import *
from .second_order import *
from scipy.signal import lfilter

def moving_average(x: np.ndarray, window_len:int = 64) -> np.ndarray:
    b = np.ones(window_len) / float(window_len)
    return lfilter(b, 1.0, x)

def short_time_cross_cumulant_4th_order(x: np.ndarray, y:np.ndarray, window_len:int = 64) -> tuple[complex, np.ndarray]:

    # use 4th order moment - pairwise 2nd moments
    m4, m4_seq = cross_complex_moment(x=x,y=y,px=1,qx=1,py=1,qy=1, central=False)
    m4_seq = moving_average(m4_seq, window_len)

    # pairwise 2nd moment: autocovariance
    T1_1, T1_1_seq = autocorrelation(x)
    T1_1_seq = moving_average(T1_1_seq, window_len)
    T1_2, T1_2_seq = autocorrelation(y)
    T1_2_seq = moving_average(T1_2_seq, window_len)
    T1 = T1_1*T1_2
    T1_seq = T1_1_seq*T1_2_seq

    # pairwise 2nd moment: covariance
    T2, T2_seq = correlation(x,y)
    T2 = np.abs(T2)**2
    T2_seq = np.abs(moving_average(T2_seq, window_len))**2

    # pairwise 2nd moment: non-conjugate covariance
    T3, T3_seq = cross_complex_moment(x=x,y=y,px=1,qx=0,py=1,qy=0, central=False)
    T3 = np.abs(T3)**2
    T3_seq = np.abs(moving_average(T3_seq, window_len))**2

    cum = m4 - T1 - T2 - T3
    cum_seq = m4_seq - T1_seq - T2_seq - T3_seq

    return np.real(cum), np.real(cum_seq)

def gemini_short_time_cross_cumulant_4th(x: np.ndarray, y: np.ndarray, window_len: int = 128) -> np.ndarray:
    """
    Computes moving-window short-time 4th-order cross-cumulant Cum(x, x*, y, y*)[t].
    """
    b = np.ones(window_len) / float(window_len)
    a = 1.0

    # Local Moving Expectations
    m4_t = lfilter(b, a, (np.abs(x) ** 2) * (np.abs(y) ** 2))
    px_t = lfilter(b, a, np.abs(x) ** 2)
    py_t = lfilter(b, a, np.abs(y) ** 2)
    r_xy_t = lfilter(b, a, x * np.conj(y))
    r_tilde_t = lfilter(b, a, x * y)

    # Cumulant calculation
    c4_t = m4_t - (px_t * py_t) - (np.abs(r_xy_t) ** 2) - (np.abs(r_tilde_t) ** 2)
    return np.real(c4_t)


