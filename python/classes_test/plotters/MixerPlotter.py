from matplotlib import pyplot as plt

from classes_test.Mixer import Mixer
from classes_test.SignalGenerator import SignalGenerator, SignalConfig
from classes_test.ComplexSignal import ComplexSignal
import numpy as np

from classes_test.plotters.ComplexSignalPlotter import SignalPlotter, AxisConfig


class MixerPlotter:
    def __init__(self):
        self.sig_plotter = SignalPlotter()
        pass

    def plot_original_iq(self, m: Mixer, ax: list[plt.Axes]):
        X = m.X
        N = X.shape[0]
        L = X.shape[1]
        for n in range(N):
            ax[n].plot(np.real(X[n, :]), label=f"orig signal {n}")
            ax[n].plot(np.imag(X[n, :]), label=f"")
            ax[n].legend()
        pass

    def plot_signal_timeseries(self, signals: list[ComplexSignal], ax: list[ plt.Axes]):
        for n in range(len(signals)):
            s = signals[n]
            axis_config = AxisConfig(title=f"{s.name}", xlabel="Time [s]", ylabel="Amplitude", grid=True)
            self.sig_plotter.plot_timeseries(s, ax[n], axis_config=axis_config)

    def plot_signal_phase(self, signals: list[ComplexSignal], ax: list[ plt.Axes]):
        for n in range(len(signals)):
            s = signals[n]
            axis_config = AxisConfig(title=f"{s.name}", xlabel="Time [s]", ylabel="Phase [degrees]", grid=True)
            self.sig_plotter.plot_phase(s, ax[n], axis_config=axis_config)

    def plot_spectrogram(self, signals: list[ComplexSignal], ax: list[ plt.Axes]):
        for n in range(len(signals)):
            s = signals[n]
            axis_config = AxisConfig(title=f"{s.name}", xlabel="Time [s]", ylabel="Frequency [Hz]", grid=True)
            self.sig_plotter.plot_spectrogram(s, ax[n], axis_config=axis_config)

    def plot_fft(self, signals: list[ComplexSignal], ax: list[ plt.Axes]):
        for n in range(len(signals)):
            s = signals[n]
            axis_config = AxisConfig(title=f"{s.name}", xlabel="Frequency [Hz]", ylabel="Magnitude", grid=True)
            self.sig_plotter.plot_fft(s, ax[n], axis_config=axis_config)

    def plot_mixed_iq(self, m: Mixer, ax: list[plt.Axes]):
        Y = m.Y
        N = Y.shape[0]
        L = Y.shape[1]
        for n in range(N):
            ax[n].plot(np.real(Y[n, :]), label=f"mixed signal {n}")
            ax[n].plot(np.imag(Y[n, :]), label=f"")
            ax[n].legend()
        pass

if __name__ == "__main__":
    m = Mixer()
    m.set_mixing_matrix(np.random.rand(3,3)+1j*np.random.rand(3,3))

    # create 3 signals
    siggen = SignalGenerator()
    s_conf_0 = SignalConfig(sample_rate=10e3, center_frequency=1000, amplitude=1, min_num_samples=1000, phase_offset=0)
    s_conf_1 = SignalConfig(sample_rate=10e3, center_frequency=100, amplitude=1, min_num_samples=1000, phase_offset=0.5)
    s_conf_2 = SignalConfig(sample_rate=10e3, center_frequency=-1000, amplitude=1, min_num_samples=1000, phase_offset=1)

    s0 = siggen.generate_CW(config=s_conf_0)
    s0.setName("CW_1")
    s1 = siggen.generate_CW(config=s_conf_1)
    s1.setName("CW_2")
    s2 = siggen.generate_CW(config=s_conf_2)
    s2.setName("CW_3")

    signals = [s0, s1, s2]
    mixed_signals = m.mix_signals(signals)

    print(f"Condition number: {m.calculate_condition_number()}")
    m.print_mixing_matrix()

    plotter = MixerPlotter()
    fig, axs = plt.subplots(3, 1, constrained_layout=True)
    plotter.plot_signal_timeseries(mixed_signals, axs)

    fig1, axs1 = plt.subplots(3, 1, constrained_layout=True)
    plotter.plot_fft(mixed_signals, axs1)

    fig2, axs2 = plt.subplots(3, 1, constrained_layout=True)
    plotter.plot_spectrogram(mixed_signals, axs2)

    plt.show()

    pass