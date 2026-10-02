"""
scripts/demo_nonstationary_cumulants.py

Simulates a non-stationary signal environment where a non-Gaussian BPSK source
turns on abruptly mid-stream in complex Gaussian noise.

Demonstrates tracking via Short-Time 4th-Order Cumulants.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import lfilter
from core.dsp.statistics.computation.cumulents import *

def generate_nonstationary_data(N_total: int = 7000):
    """
    Generates non-stationary 2-channel complex IQ data.
    """
    np.random.seed(42)

    # 1. Background Complex Gaussian AWGN Noise (2 channels)
    noise = (np.random.randn(2, N_total) + 1j * np.random.randn(2, N_total)) / np.sqrt(2)

    # 2. Non-Gaussian Signal (BPSK symbols: +1 or -1)
    bpsk_symbols = np.random.choice([-1, 1], size=N_total).astype(np.complex128)

    # Mix into channels with spatial array response
    steering_vec = np.array([[1.0], [0.8 + 0.6j]])
    signal_channels = steering_vec @ bpsk_symbols.reshape(1, -1)

    # 3. Create non-stationary timeline (Signal active only between N=2000 and N=5000)
    active_mask = np.zeros(N_total)
    active_mask[2000:5000] = 1.0

    X = noise + signal_channels * active_mask
    return X, active_mask


def short_time_cross_cumulant_4th(x: np.ndarray, y: np.ndarray, window_len: int = 128) -> np.ndarray:
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
    return c4_t


if __name__ == "__main__":
    N_total = 7000
    window_len = 5

    # Generate non-stationary data
    X, active_mask = generate_nonstationary_data(N_total)
    x0, x1 = X[0, :], X[1, :]

    # Compute short-time auto-cumulant on Channel 0 and cross-cumulant (Channel 0 & 1)
    c4_auto = short_time_cross_cumulant_4th(x0, x0, window_len=window_len)
    c4_cross = short_time_cross_cumulant_4th(x0, x1, window_len=window_len)

    my_c4_auto, my_c4_auto_seq = short_time_cross_cumulant_4th_order(x0, x0, window_len=window_len)
    my_c4_cross, my_c4_cross_seq = short_time_cross_cumulant_4th_order(x0, x1, window_len=window_len)

    # Plotting
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)

    # Plot 1: Raw IQ Signal Amplitude (Real Part)
    axes[0].plot(x0.real, color='gray', alpha=0.5, label='Raw Channel 0 Real(IQ)')
    axes[0].plot(active_mask * 2, color='red', linestyle='--', label='BPSK Active Region')
    axes[0].set_ylabel('Amplitude')
    axes[0].set_title('Non-Stationary Signal Environment (Gaussian Noise + Transient BPSK)')
    axes[0].legend(loc='upper right')
    axes[0].grid(True, alpha=0.3)

    # Plot 2: Short-Time Auto-Cumulant Cum(X0, X0*, X0, X0*)
    axes[1].plot(c4_auto.real, color='navy', label=f'Auto-Cumulant c4[t] (Window={window_len})')
    axes[1].plot(my_c4_auto_seq.real, color='red', label=f'My-Auto-Cumulant c4[t] (Window={window_len})')
    axes[1].axhline(0, color='black', linestyle=':', label='Gaussian Benchmark (0.0)')
    axes[1].set_ylabel('Auto Cumulant')
    axes[1].set_title('Short-Time Auto-Kurtosis Trajectory')
    axes[1].legend(loc='upper right')
    axes[1].grid(True, alpha=0.3)

    # Plot 3: Short-Time Cross-Cumulant Cum(X0, X0*, X1, X1*)
    axes[2].plot(c4_cross.real, color='darkgreen', label=f'Cross-Cumulant c4[t] (Window={window_len})')
    axes[2].plot(my_c4_cross_seq.real, color='red', label=f'My-Cross-Cumulant c4[t] (Window={window_len})')
    axes[2].axhline(0, color='black', linestyle=':', label='Gaussian Benchmark (0.0)')
    axes[2].set_xlabel('Snapshot Index (Time t)')
    axes[2].set_ylabel('Cross Cumulant')
    axes[2].set_title('Short-Time Cross-Cumulant Trajectory (Channel 0 x Channel 1)')
    axes[2].legend(loc='upper right')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()