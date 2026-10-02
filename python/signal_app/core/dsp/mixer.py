import numpy as np
from .signal_new import Signal

class Mixer:
    """Class for performing generic linear mixing operations on a set of Signals"""
    def __init__(self):
        self.A: np.ndarray = None # mixing matrix
        self.X: np.ndarray = None # datamatrix input of signals
        self.Y: np.ndarray = None # datamatrix output of mixing
        self.A_n: np.ndarray= None

        pass

    @property
    def condition_number(self):
        return np.linalg.cond(self.A)

    @property
    def inverse_A(self):
        return np.linalg.pinv(self.A)

    def set_mixing_matrix(self, mixing_matrix: np.ndarray):
        self.A = mixing_matrix
        print(f"Setting mixing matrix with condition number: {self.condition_number}")

    def mix_signals(self, signals: list[Signal]) -> list[Signal]:

        N = len(signals)
        L = signals[0].num_samples
        M, Z = np.shape(self.A)
        print(f"\n Mixing {N} Signals {L} length signals, expected output {M}x{Z}\n")
        X = np.zeros((N, L), dtype=np.complex128)
        for n in range(N):
            X[n, :] = signals[n].iq
        self.Y = self.A @ X

        # extract signal events and make a master event list for all
        print(f"\n Constructing master events with {len(signals)} signals\n")
        events = []
        for sig in signals:
            print(f"   there are {len(sig.events)} events in signal {sig.label}\n")
            for ev in sig.events:
                events.append(ev)

        print(f"\n Constructing return")
        return [Signal(iq=self.Y[m, :],
                       sample_rate=signals[0].fs,
                       events=events,
                       label=f"mixed signal {m}"
                       ) for m in range(M)]

    def describe(self):
        def print_matrix(matrix: np.ndarray):
            for row in matrix:
                for val in row:
                    print(f"{val:.2f} | ", end=" ")
                print("")

        print(f"Mixing matrix: ")
        print_matrix(self.A)
        print(f"Condition number: {self.condition_number}")
        print(f"Inverse of mixing matrix: ")
        print_matrix(self.inverse_A)

if __name__ == "__main__":
    from iq_signal import Signal
    from signal_generators.sig_gen import SignalGenerator, SignalConfig
    import matplotlib.pyplot as plt

    mixer = Mixer()
    mixer.set_mixing_matrix(np.array([[1, 2+1j], [0.3-2j, 4]]))
    mixer.describe()

    sigGen = SignalGenerator()
    config_lfm = SignalConfig(sample_rate=10e3,
                              center_frequency=0,
                              lfm_f_lower=-3000,
                              lfm_f_upper=3000,
                              amplitude=1,
                              min_num_samples=1000,
                              phase_offset=0)
    config_noise = SignalConfig(sample_rate=10e3,
                                center_frequency=0,
                                noise_f_lower=-4000,
                                noise_f_upper=4000,
                                amplitude=100,
                                min_num_samples=1000,
                                phase_offset=0)

    signal_noise: Signal = sigGen.generate_Noise(config=config_noise)
    signal_lfm: Signal = sigGen.generate_LFM(config=config_lfm)

    fig, ax = plt.subplots(2, 2, figsize=(10, 10))
    # original signals:
    ax[0,0].plot(signal_noise.time_vector, signal_noise.iq.real)
    ax[0,0].plot(signal_noise.time_vector, signal_noise.iq.imag)
    ax[0,0].set_title("Noise")
    ax[0,0].set_xlabel("Time [s]")
    ax[0,0].set_ylabel("Amplitude")
    ax[0,0].grid(True)
    ax[1,0].plot(signal_lfm.time_vector, signal_lfm.iq.real)
    ax[1,0].plot(signal_lfm.time_vector, signal_lfm.iq.imag)
    ax[1,0].set_title("LFM")
    ax[1,0].set_xlabel("Time [s]")
    ax[1,0].set_ylabel("Amplitude")
    ax[1,0].grid(True)

    # mixed signals:
    mixed_signals = mixer.mix_signals([signal_noise, signal_lfm])
    ax[0,1].plot(mixed_signals[0].time_vector, mixed_signals[0].iq.real)
    ax[0,1].plot(mixed_signals[0].time_vector, mixed_signals[0].iq.imag)
    ax[0,1].set_title("Mixed 0")
    ax[0,1].set_xlabel("Time [s]")
    ax[0,1].set_ylabel("Amplitude")
    ax[0,1].grid(True)
    ax[1,1].plot(mixed_signals[1].time_vector, mixed_signals[1].iq.real)
    ax[1,1].plot(mixed_signals[1].time_vector, mixed_signals[1].iq.imag)
    ax[1,1].set_title("Mixed 1")
    ax[1,1].set_xlabel("Time [s]")
    ax[1,1].set_ylabel("Amplitude")
    ax[1,1].grid(True)

    plt.show()