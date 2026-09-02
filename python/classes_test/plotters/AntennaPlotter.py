from classes_test.AntennaMixer import AntennaMixer
from classes_test.plotters.ComplexSignalPlotter import SignalPlotter
from classes_test.plotters.MixerPlotter import MixerPlotter
from classes_test.SignalGenerator import SignalGenerator, SignalConfig

import matplotlib.pyplot as plt
import numpy as np

class AntennaPlotter(MixerPlotter):
    def __init__(self):
        super().__init__()
        pass

    def plot_beamformed_signal(self, a:AntennaMixer, ax: plt.Axes):
        sig = np.squeeze(a.B)
        ax.plot(np.real(sig), label="Real")
        ax.plot(np.imag(sig), label="Imag")
        ax.legend()
        ax.grid(True)
        ax.set_xlabel("Sample Index")
        ax.set_ylabel("Amplitude")
        ax.set_title("Beamformed Signal")

    def plot_scanned_response(self, a:AntennaMixer, ax: plt.Axes):
        angles, resp, beam_resp = a.compute_scanned_response()
        ax.plot(angles*180/np.pi, resp)
        ax.plot(angles*180/np.pi, beam_resp)
        ylim = (np.min(resp)-10, np.max(resp)+10)

        # plot signal names and types in text box on doa
        # get resp vector value at specific angle index closest to doas
        resp_at_doas = [resp[np.argmin(np.abs(angles - doa))] for doa in a.signal_doas]
        print(np.shape(resp_at_doas))
        bbox = dict(boxstyle="square", fc="w", ec="0.5", alpha=0.9)
        for n in range(len(a.signal_doas)):
            print(f"resp value at doa {a.signal_doas[n]*180/np.pi} is {resp_at_doas[n]}")
            ax.plot([a.signal_doas[n]*180/np.pi,a.signal_doas[n]*180/np.pi], [ylim[0], ylim[1]], "--", color="red")
            ax.text(a.signal_doas[n]*180/np.pi, resp_at_doas[n],
                    f"{a.signal_dict[n]['name']}\n({a.signal_dict[n]['source']})",
                    fontsize=8, ha="center", va="bottom",
                    bbox=bbox)

        #ax.set_ylim(ylim)
        ax.grid(True)
        ax.set_xlabel("Angle [degrees]")
        ax.set_ylabel("Power [dB]")
        ax.set_title("Scanned Response")

        pass

if __name__ == "__main__":
    plotter = AntennaPlotter()
    a = AntennaMixer(num_elements=20)

    siggen = SignalGenerator()

    config1 = SignalConfig(sample_rate=10e3,
                          center_frequency=0,
                          SNR=-3,
                          lfm_f_lower=-3000,
                          lfm_f_upper=3000,
                          noise_f_lower=-1000,
                          noise_f_upper=2000,
                          amplitude=0.000,
                          min_num_samples=1000,
                          phase_offset=0)
    config2 = SignalConfig(sample_rate=10e3,
                           center_frequency=0,
                           SNR=-3,
                           lfm_f_lower=-3000,
                           lfm_f_upper=3000,
                           noise_f_lower=-4500,
                           noise_f_upper=4500,
                           amplitude=1,
                           min_num_samples=1000,
                           phase_offset=0)
    config3 = SignalConfig(sample_rate=10e3,
                           center_frequency=0,
                           SNR=-3,
                           lfm_f_lower=-3000,
                           lfm_f_upper=3000,
                           noise_f_lower=-300,
                           noise_f_upper=300,
                           amplitude=0.01,
                           min_num_samples=1000,
                           phase_offset=0)
    s0 = siggen.generate_Noise(config=config1)
    s0.setName("Noise 0")
    s0.setSource("Interference")
    s1 = siggen.generate_Noise(config=config2)
    s1.setName("Noise 1")
    s1.setSource("Interference")
    s2 = siggen.generate_LFM(config=config3)
    s2.setName("LFM")
    s2.setSource("Desired")

    signals = [s0, s1, s2]
    angles = np.radians([-10, 10, 25])
    a.antenna_mixing_matrix(angles=angles)
    mixed_signals = a.mix_signals(signals)
    a.beamform(style="adaptive",weighting=None, steering_doa=25)
    b_out = s2.copy()
    b_out.setName("Beamformed Signal")
    b_out.iq = np.squeeze(a.B)
    sig_plotter = SignalPlotter()

    # plot functions
    fig, ax = plt.subplots(1, 1, constrained_layout=True)
    plotter.plot_scanned_response(a=a, ax=ax)

    #fig1, axs = plt.subplots(1, 3, constrained_layout=True)
    #plotter.plot_spectrogram(mixed_signals, ax=axs)


    #fig2, axs1 = plt.subplots(1, 1, constrained_layout=True)
    #plotter.plot_beamformed_signal(a, ax=axs1)

    fig3, axs3 = plt.subplots(1, 1, constrained_layout=True)
    sig_plotter.plot_spectrogram(b_out, ax=axs3)

    plt.show()
    pass