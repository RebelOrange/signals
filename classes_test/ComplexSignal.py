import numpy as np
import matplotlib.pyplot as plt
from typing import TypedDict
from scipy.signal import ShortTimeFFT
from scipy.signal.windows import gaussian


class ComplexSignal:
    def __init__(self, iq: np.ndarray, length: int, sample_rate: float, signal_type: str, time_vector: np.ndarray, name: str = "Signal", source: str = "Unknown"):
        self.iq = iq
        self.length = length
        self.sample_rate = sample_rate
        self.signal_type = signal_type
        self.time_vector = time_vector
        self.name = name
        self.source = source
        pass

    def get_signal(self):
        pass

    def setSource(self, source: str):
        self.source = source

    def setName(self, name: str):
        self.name = name

    def copy(self):
        return ComplexSignal(iq=self.iq.copy(), length=self.length, sample_rate=self.sample_rate, signal_type=self.signal_type, time_vector=self.time_vector.copy(), name=self.name)

    def get_FFT(self, units:str = "dB", n:int = 1) -> tuple[np.ndarray, np.ndarray]:
        """Returns FFT and frequency vector of signal with specified units [dB, complex] and number of samples."""
        n_samps = max(n, self.length)
        if units == "dB":
            F = 20*np.log10(np.abs(np.fft.fft(self.iq, n_samps)))
        elif units == "complex":
            F= np.fft.fft(self.iq, n_samps)
        else:
            raise ValueError("Invalid units. Must be 'dB' or 'linear'.")

        f = np.fft.fftfreq(len(F), 1/self.sample_rate)
        return F, f

    def get_SFT(self, n:int = 128, units:str = "dB") -> tuple[np.ndarray, np.ndarray]:
        """Returns Short Time Fourier Transform of signal with specified units [dB, linear] and ax.imshow extent"""
        g_std = 8
        w= gaussian(50, std=g_std, sym=True)
        N = min(n, self.length)
        SFT = ShortTimeFFT(w, hop=10, fs = self.sample_rate, mfft=N, fft_mode="centered")
        Sx = SFT.stft(self.iq)

        # extra returns
        extent = SFT.extent(self.length)

        # handle units
        if units == "dB":
            Sx = 10*np.log10(np.abs(Sx))
        elif units == "linear":
            pass
        return Sx, extent

    def get_Phase(self, units:str = "degrees", unwrapped:bool=True) -> np.ndarray:
        """Returns phase of signal in specified units [degrees, radians]."""
        phase = np.angle(self.iq)
        if unwrapped:
            phase = np.unwrap(phase)
        if units == "degrees":
            phase = np.degrees(phase)
        elif units == "radians":
            pass

        return phase



if __name__ == "__main__":
    from classes_test.SignalGenerator import SignalGenerator, SignalConfig
    config = SignalConfig(sample_rate=10e3, center_frequency=0, lfm_f_lower=-3000, lfm_f_upper=3000, noise_f_lower=-30, noise_f_upper=30,amplitude=1, min_num_samples=1000, phase_offset=0)
    print(config)
    sigGen = SignalGenerator()
    signal = sigGen.generate_Noise(config=config)
    signal.plot_signal()