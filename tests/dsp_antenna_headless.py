import numpy as np
from matplotlib import pyplot as plt

from core.antennas.classic.ULA import ULA
from core.dsp.iq_signal import Signal
from core.dsp.mixer import Mixer
from signal_generators.sig_gen import SignalGenerator, SignalConfig

from mpl.dsp.signal_plotter import *
from mpl.antenna_plotter import *

import matplotlib
#matplotlib.use("Qt5Agg")

if __name__ == "__main__":
    sigGen = SignalGenerator()
    a = ULA(num_elements=20)
    print(a.num_elements)
    print(a.positions)
    print(a.weights)

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

    sig_list = [signal_noise.iq, signal_lfm.iq]
    doa_list = [(0.0, 0.0), (25.0, 0.0)]

    a.receive(sig_list, doa_list)
    y = a.beamform()

    fig, ax = plt.subplots(3,1)

    plot_iq_timeseries(signal_lfm.time_vector, signal_lfm.iq, ax=ax[0])
    plot_iq_timeseries(signal_lfm.time_vector, y, ax=ax[1])
    y = a.beamform(steering_doa=(25.0, 0.0))
    plot_iq_timeseries(signal_lfm.time_vector, y, ax=ax[2])

    fig2, ax2 = plt.subplots(1,1)
    S, ex = signal_lfm.STFT()
    plot_spectrogram(S=S, extent=ex, ax=ax2, colorbar=True)

    fig1, ax1 = plt.subplots(1,1)#, subplot_kw={"projection": "3d"})
    x, y = a.scan_response()
    #plot_scan_response(y, x, ax=ax1)
    plot_element_positions(a.positions, ax=ax1)

    plt.show()
