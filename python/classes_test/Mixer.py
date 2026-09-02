import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import subplot_mosaic

from classes_test.ComplexSignal import ComplexSignal
from classes_test.SignalGenerator import SignalConfig, SignalGenerator
from classes_test.plotters.ComplexSignalPlotter import SignalPlotter


class Mixer:
    """Class for performing generic linear mixing operations on a set of ComplexSignals"""
    def __init__(self):
        self.A = None
        self.Y = None
        self.X = None
        self.condition_number = 0
        self.inverse_H = None
        self.signal_dict = {}
        pass

    def set_mixing_matrix(self, mixing_matrix: np.ndarray):
        self.A = mixing_matrix

    def get_mixing_matrix(self) -> np.ndarray:
        return self.A

    def mix_signals(self, signals: list[ComplexSignal]) -> list[ComplexSignal]:
        """Mixes a list of ComplexSignals using the mixing matrix, returning a list of mixed signals,
        with length equal to the dimension of the mixing matrix"""

        # store signal names, indices, and types in a dictionary for future reference
        for n in range(len(signals)):
            self.signal_dict[n] = {"name": signals[n].name, "type": signals[n].signal_type, "source": signals[n].source}

        # arrange N signals of length L in an NxL matrix S
        N = len(signals)
        L = signals[0].length
        X = np.zeros((N, L), dtype=np.complex128)
        for n in range(N):
            X[n, :] = signals[n].iq

        self.X = X

        Y = np.matmul(self.A, X)
        # save mixed signals internally as matrix
        self.Y = Y


        # gereate list of mixed signals using parameters from first signal
        mixed_signals = []
        for n in range(N):
            mixed_signals.append(ComplexSignal(iq=Y[n, :],
                                               length=L,
                                               sample_rate=signals[0].sample_rate,
                                               signal_type=f"mixed signal",
                                               time_vector=signals[0].time_vector,
                                               name=f"mixed signal {n}"))
        return mixed_signals

    def unmix_signals(self, signals: list[ComplexSignal], B: np.ndarray = None) -> list[ComplexSignal]:
        N = len(signals)
        L = signals[0].length
        if B is None:
            B = self.inverse_A
        X_est = np.matmul(B, self.Y)
        self.X_est = X_est
        unmixed_signals = []
        for n in range(N):
            unmixed_signals.append(ComplexSignal(iq=X_est[n, :],
                                                  length=L,
                                                  sample_rate=signals[0].sample_rate,
                                                  signal_type="unmixed signal",
                                                  time_vector=signals[0].time_vector,
                                                  name=f"unmixed signal {n}"))
        return unmixed_signals

    def calculate_condition_number(self):
        """Calculates the condition number of the mixing matrix"""
        self.condition_number = np.linalg.cond(self.A)
        return self.condition_number

    def calculate_inverse(self):
        """Calculates the inverse of the mixing matrix"""
        self.inverse_A = np.linalg.pinv(self.A)
        return self.inverse_A

    def print_mixing_matrix(self):
        M = self.get_mixing_matrix()
        print(f"Mixing matrix: ")
        for row in M:
            for val in row:
                print(f"{val:.2f} | ", end=" ")
            print("")

if __name__ == "__main__":
    m = Mixer()
    m.set_mixing_matrix(np.eye(3))

    # create 3 signals
    siggen = SignalGenerator()
    s_conf_0 = SignalConfig(sample_rate=10e3, center_frequency=1000, amplitude=1, min_num_samples=1000, phase_offset=0)
    s_conf_1 = SignalConfig(sample_rate=10e3, center_frequency=100, amplitude=1, min_num_samples=1000, phase_offset=0.5)
    s_conf_2 = SignalConfig(sample_rate=10e3, center_frequency=-1000, amplitude=1, min_num_samples=1000, phase_offset=1)

    s0 = siggen.generate_CW(config=s_conf_0)
    s1 = siggen.generate_CW(config=s_conf_1)
    s2 = siggen.generate_CW(config=s_conf_2)

    signals = [s0, s1, s2]
    mixed_signals = m.mix_signals(signals)

    print(f"Condition number: {m.calculate_condition_number()}")


    s_plotter = SignalPlotter()
    fig, axs = subplot_mosaic([["m1","m2","m3"]], constrained_layout=True)
    s_plotter.plot_fft(mixed_signals[0], ax=axs["m1"])
    s_plotter.plot_fft(mixed_signals[1], ax=axs["m2"])
    s_plotter.plot_fft(mixed_signals[2], ax=axs["m3"])

    plt.show()




