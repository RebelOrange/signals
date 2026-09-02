import numpy as np
from typing import TypedDict
from matplotlib import pyplot as plt
from scipy.signal import spectrogram

from classes_test.SignalGenerator import SignalGenerator, SignalConfig
from classes_test.ComplexSignal import ComplexSignal

class AxisConfig(TypedDict, total=False):
    title: str
    xlabel: str
    ylabel: str
    grid: bool

class SignalPlotter:
    def __init__(self):
        pass

    def plot_timeseries(self, signal: ComplexSignal, ax: plt.Axes, axis_config: AxisConfig = None):
        if axis_config is None:
            axis_config = AxisConfig(title="Time Series", xlabel="Time [s]", ylabel="Amplitude", grid=True)
        # timeseries
        ax.plot(signal.time_vector, np.real(signal.iq), label="Real")
        ax.plot(signal.time_vector, np.imag(signal.iq), label="Imag")
        ax.legend()
        ax.grid(axis_config["grid"])
        ax.set_title(axis_config["title"])
        ax.set_xlabel(axis_config["xlabel"])
        ax.set_ylabel(axis_config["ylabel"])

    def plot_xcorr(self, sig1: ComplexSignal, sig2: ComplexSignal, ax: plt.Axes, axis_config: AxisConfig = None):
        if axis_config is None:
            axis_config = AxisConfig(title="Cross Correlation", xlabel="Lags", ylabel="Amplitude", grid=True)
        xcorr = np.correlate(sig1.iq, sig2.iq, mode="full")
        xcorr /= np.max(np.abs(xcorr))
        lags = np.arange(-len(sig1.iq)+1, len(sig2.iq))
        ax.plot(lags, xcorr)
        ax.grid(axis_config["grid"])
        ax.set_title(axis_config["title"])
        ax.set_xlabel(axis_config["xlabel"])
        ax.set_ylabel(axis_config["ylabel"])

    def plot_spectrogram(self, signal: ComplexSignal, ax: plt.Axes, axis_config: AxisConfig = None):
        if axis_config is None:
            axis_config = AxisConfig(title="Spectrogram", xlabel="Time [s]", ylabel="Frequency [Hz]", grid=True)
        Sx, extent = signal.get_SFT()
        ax.imshow(Sx, aspect="auto", extent=extent, origin="lower", cmap="jet")
        ax.set_xlabel(axis_config["xlabel"])
        ax.set_ylabel(axis_config["ylabel"])
        ax.grid(axis_config["grid"])
        ax.set_title(axis_config["title"])

    def plot_fft(self, signal: ComplexSignal, ax: plt.Axes, axis_config: AxisConfig = None):
        if axis_config is None:
            axis_config = AxisConfig(title="FFT", xlabel="Frequency [MHz]", ylabel="Power [dB]", grid=True)
        F, f = signal.get_FFT("dB", n=1024)

        ax.plot(f/1e6, F, label="")
        ax.set_xlabel(axis_config["xlabel"])
        ax.set_ylabel(axis_config["ylabel"])
        ax.grid(axis_config["grid"])
        ax.set_ylim([np.max(F)-80, np.max(F)+10])
        ax.set_title(axis_config["title"])

    def plot_phase(self, signal: ComplexSignal, ax: plt.Axes, axis_config: AxisConfig = None, unwrapped:bool=True):
        if axis_config is None:
            axis_config = AxisConfig(title="Phase", xlabel="Time [s]", ylabel="Phase [degrees]", grid=True)
        P = signal.get_Phase(units="degrees", unwrapped=unwrapped)
        ax.plot(signal.time_vector, P, label="Phase")
        ax.set_xlabel(axis_config["xlabel"])
        ax.set_ylabel(axis_config["ylabel"])
        ax.grid(axis_config["grid"])
        ax.set_title(axis_config["title"])

    def plot_histogram(self, signal: ComplexSignal, ax: plt.Axes, axis_config: AxisConfig = None, bins:int=128):
        if axis_config is None:
            axis_config = AxisConfig(title="Histogram", xlabel="Real", ylabel="Imag", grid=True)

        ax.hist2d(np.real(signal.iq), np.imag(signal.iq), bins=128, cmap="jet")
        ax.set_xlabel(axis_config["xlabel"])
        ax.set_ylabel(axis_config["ylabel"])
        ax.grid(axis_config["grid"])
        ax.set_title(axis_config["title"])

    def plot_overview(self, signal: ComplexSignal, axs: tuple[plt.Axes, plt.Axes, plt.Axes,plt.Axes], title: str = "Signal Overview", fft_type: str = "fft"):
        # plots a 2x2 grid of subplots from subplots_mosaic, with time domain, fft, signal phase, and complex histogram.
        # FFT is switchable to spectrogram
        axis_config = None
        self.plot_timeseries(signal, axs[0], axis_config=axis_config)

        # FFT/Spectrogram
        if fft_type == "fft":
            axis_config = None
            self.plot_fft(signal, axs[1], axis_config=axis_config)
        elif fft_type == "spectrogram":
            axis_config = None
            self.plot_spectrogram(signal, axs[1], axis_config=axis_config)

        # Phase
        axis_config = None
        self.plot_phase(signal, axs[2], axis_config=axis_config)

        # Complex Histogram
        axis_config = None
        self.plot_histogram(signal, axs[3], axis_config=axis_config)



if __name__ == "__main__":
    plotter = SignalPlotter()
    siggen = SignalGenerator()
    config = SignalConfig(sample_rate=10e3,
                          center_frequency=0,
                          SNR=-3,
                          lfm_f_lower=-3000,
                          lfm_f_upper=3000,
                          noise_f_lower=-30,
                          noise_f_upper=30,
                          amplitude=1,
                          min_num_samples=1000,
                          phase_offset=0)
    signal = siggen.generate_LFM(config=config)
    ktB = siggen.generate_system_noise(config=config)

    signal_w_ktB = signal.copy()
    signal_w_ktB.iq += ktB.iq

    signal.setName("Original Signal")
    signal_w_ktB.setName(f"Signal with System Noise SNR: {config['SNR']}dB")

    fig, axs = plt.subplot_mosaic([["time", "fft"], ["phase", "hist"]],
                                  constrained_layout=True)
    ax_tuple = (axs["time"], axs["fft"], axs["phase"], axs["hist"])
    plotter.plot_overview(signal, axs=ax_tuple, title="Original Signal", fft_type="spectrogram")

    fig1, axs1 = plt.subplot_mosaic([["time", "fft"], ["phase", "hist"]],
                                    constrained_layout=True)
    ax_tuple1 = (axs1["time"], axs1["fft"], axs1["phase"], axs1["hist"])
    plotter.plot_overview(signal_w_ktB, axs=ax_tuple1, title="Signal+Noise", fft_type="spectrogram")

    fig2, axs2 = plt.subplot_mosaic([["xcorr"]],
                                    constrained_layout=True)

    plotter.plot_xcorr(signal, signal_w_ktB, ax=axs2["xcorr"])


    plt.show()

