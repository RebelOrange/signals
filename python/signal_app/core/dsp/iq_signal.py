import numpy as np
from scipy.signal import ShortTimeFFT
import copy

# for abstract class
from abc import ABC, abstractmethod

from scipy.signal.windows import gaussian

from mpl.dsp.stat_plotters.moment_plotter import plot_moment
from mpl.dsp.stat_plotters.pair_plotter import pair_plot_complex_signals


class BaseSignal(ABC):
    def __init__(self, iq: np.ndarray, fs: float, fc: float=0,
                 label:str = "signal", mask: np.ndarray = None):
        self.iq = iq
        self.fs = fs
        self.fc = fc
        self.label = label
        self.binary_mask = mask

    @abstractmethod
    def __add__(self, other: "BaseSignal") -> "BaseSignal":
        pass

    @property
    def variance(self):
        return np.dot(self.iq, self.iq.conj())/self.num_samples

    @property
    def power(self):
        return self.variance

    @property
    def num_samples(self):
        return self.iq.shape[0]

    @property
    def duration(self):
        return self.num_samples / self.fs

    @property
    def time_vector(self):
        return np.arange(0, self.duration, 1/self.fs)

    @property
    def sample_vector(self):
        return np.arange(0, self.num_samples)

    @property
    def fft(self) -> tuple[np.ndarray, np.ndarray]:
        """Returns the FFT of the signal and the corresponding frequency vector."""
        return np.fft.fft(self.iq), np.fft.fftfreq(self.num_samples, 1/self.fs)

    @property
    def fft_dB(self) -> tuple[np.ndarray, np.ndarray]:
        """Returns the FFT of the signal and the corresponding frequency vector."""
        F = 20*np.log10(np.abs(self.fft[0]))
        f = self.fft[1]
        return F, f

    def STFT(self, n:int = 128, g_std:int = 8, window_L:int = 50, hop:int = 10):
        """Returns the STFT of the signal and the corresponding frequency vector."""
        g_std = g_std
        w = gaussian(window_L, std=g_std, sym=True)
        N = min(n, self.num_samples)
        SFT = ShortTimeFFT(w, hop=hop, fs = self.fs, mfft=N, fft_mode="centered")
        Sx = SFT.stft(self.iq)
        return Sx, SFT.extent(self.num_samples)

    @property
    def phase(self):
        return np.angle(self.iq)

class Signal(BaseSignal):

    def __add__(self, other: "Signal") -> "Signal":
        if not isinstance(other, BaseSignal):
            return NotImplemented
        if self.fs != other.fs:
            raise ValueError(f"Signal sample rates are different\n"
                             f"S1 has {self.fs} Hz and S2 has {other.fs} Hz")
        if self.num_samples != other.num_samples:
            raise ValueError(f"Signal vector lengths are different\n"
                             f"S1 has {self.num_samples} samples and S2 has {other.num_samples} samples")

        combined_iq = self.iq + other.iq
        return Signal(combined_iq, self.fs, fc=0, label=f"{self.label}+{other.label}")

    pass

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from signal_generators.sig_gen import SignalGenerator, SignalConfig
    from mpl.dsp.signal_plotter import *

    sigGen = SignalGenerator()
    config_lfm = SignalConfig(sample_rate=10e3,
                              lfm_f_lower=-1000,
                              lfm_f_upper=1000,
                              amplitude=1,
                              SNR=10,
                              min_num_samples=1000,
                              mask_type="sample",
                              start_sample=1200,
                              stop_sample=2500,
                              total_samples=3000
                              )

    des_sig: Signal = sigGen.generate_LFM(config=config_lfm)
    # calculate desired variance for -6dB J2S
    req_var = 2*des_sig.variance

    print(f"req_var: {req_var}")

    config_jamming = SignalConfig(sample_rate=10e3,
                                noise_f_lower=-3000,
                                noise_f_upper=2000,
                                amplitude=1,
                                noise_var=req_var,
                                min_num_samples=1000,
                                mask_type="sample",
                                start_sample=600,
                                stop_sample=1800,
                                total_samples=3000)

    jamming_sig: Signal = sigGen.generate_Noise(config=config_jamming)
    des_sig: Signal = sigGen.generate_LFM(config=config_lfm)
    ktb_sig: Signal = sigGen.generate_system_noise(config = config_lfm)
    rx_sig = des_sig + jamming_sig + ktb_sig

    pair_plot_complex_signals(rx_sig.iq, des_sig.iq)

    fig, ax = plt.subplots(1, 1)
    plot_moment(rx_sig.iq, 2, 2, ax=ax)

    fig, ax = plt.subplots(1, 2)
    S, ex = rx_sig.STFT()
    plot_spectrogram(S, ex, ax=ax[0])
    plot_iq_timeseries(rx_sig.time_vector, rx_sig.iq, ax=ax[1])

    # plotting ts, fft, phase
    fig, ax = plt.subplots(1, 3, figsize=(10, 10))
    ax[0].plot(rx_sig.sample_vector, rx_sig.iq.real)
    ax[0].plot(rx_sig.sample_vector, rx_sig.iq.imag)
    ax[0].set_title("IQ")
    ax[0].set_xlabel("Time [s]")
    ax[0].set_ylabel("Amplitude")
    ax[0].grid(True)

    F, f = rx_sig.fft_dB
    ax[1].plot(f / 1e3, F)
    ax[1].set_title("FFT")
    ax[1].set_xlabel("Frequency [kHz]")
    ax[1].set_ylabel("Power [dB]")
    ax[1].grid(True)

    P = rx_sig.phase
    ax[2].plot(rx_sig.sample_vector, np.degrees(np.unwrap(rx_sig.phase)))
    ax[2].set_title("Phase")
    ax[2].set_xlabel("Time [s]")
    ax[2].set_ylabel("Phase [degrees]")
    ax[2].grid(True)

    plt.show()