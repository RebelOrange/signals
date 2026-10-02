import numpy as np

from scipy.signal.windows import gaussian
from scipy.signal import ShortTimeFFT

class SignalAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def STFT(x:np.array, fs:float, n:int=128, g_std:int=8, window_L:int=50, hop: int=10):

        w = gaussian(window_L, std=g_std, sym=True)
        N = min(n, len(x))
        SFT = ShortTimeFFT(w, hop=hop, fs=fs, mfft=N, fft_mode="centered")
        Sx = SFT.stft(x)
        return Sx, SFT.extent(len(x))

    @staticmethod
    def FFT(x, nfft:int=256):
        N = min(nfft, len(x))
        return np.fft.fft(x, n=N)


    @staticmethod
    def fft_freqs(x: np.ndarray, fs: float, nfft:int=256):
        N = min(nfft, len(x))
        return np.fft.fftfreq(N, 1.0/fs)/N

    @staticmethod
    def phase(x: np.ndarray):
        return np.angle(x)

    @staticmethod
    def xcorr(x:np.ndarray, y:np.ndarray, max_lag:int = 100):
        xcorr = np.correlate(x, y, mode='full')
        xcorr /= len(xcorr)
        zero_lag = len(y) - 1
        start = max(0, zero_lag - max_lag)
        end = min(len(xcorr), zero_lag + max_lag + 1)
        lags = np.arange(start - zero_lag, end - zero_lag)
        return xcorr[start:end], lags

    @staticmethod
    def eigenvalue_decomp(x:np.ndarray):
        R = x@x.conj().T / len(x)
        eigenvalues, eigenvectors = np.linalg.eig(R)
        idx = eigenvalues.argsort()[::-1]
        eigenvalues_sort = eigenvalues[idx]
        eigenvectors_sort = eigenvectors[:,idx]
        return eigenvalues_sort, eigenvectors_sort



    @staticmethod
    def matched_filter(x:np.ndarray, template:np.ndarray):
        mf = np.correlate(x, template, mode='same')
        mf /= len(mf)
        return mf