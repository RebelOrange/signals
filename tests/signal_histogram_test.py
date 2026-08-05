from core.dsp.statistics.computation import histogram as h
from core.dsp.iq_signal import Signal
from core.dsp.signal_generators.sig_gen import SignalGenerator, SignalConfig

import matplotlib.pyplot as plt
import numpy as np

from mpl.dsp.signal_plotter import *
from mpl.dsp.stat_plotters.complex_distrobution import plot_complex_distribution
from mpl.dsp.stat_plotters.pair_plotter import pair_plot_complex_signals
from mpl.dsp.stat_plotters.moment_plotter import *

if __name__ == "__main__":
    sigGen = SignalGenerator()
    config_noise = SignalConfig(sample_rate=10e3,
                                center_frequency=0,
                                noise_f_lower=-4000,
                                noise_f_upper=4000,
                                lfm_f_lower=-1000,
                                lfm_f_upper=1000,
                                amplitude=0.1,
                                min_num_samples=1000,
                                phase_offset=0)

    config_ktb_noise = SignalConfig(sample_rate=10e3,
                                center_frequency=0,
                                noise_f_lower=-5000,
                                noise_f_upper=5000,
                                amplitude=10,
                                min_num_samples=1000,
                                phase_offset=0)

    config_barker = SignalConfig(
        sample_rate=10e3,
        center_frequency=0,
        amplitude=0.01,
        min_num_samples=1000,
        phase_offset=0,
        bpsk_code=sigGen.barker_code(13),
    )

    s1 = sigGen.generate_LFM(config=config_noise)
    #del s1
    #s1 = sigGen.generate_BPSK(config=config_barker)
    ktb = sigGen.generate_Noise(config=config_ktb_noise)

    f_shift = 0.0
    phase_shift = 45.0
    e_shift = np.exp(1j * (2 * np.pi * f_shift * s1.time_vector + phase_shift*np.pi/180))
    s1_noisy = s1.iq.copy()*e_shift + ktb.iq.copy()

    # cross correlation
    plt.plot(np.abs(np.correlate(s1_noisy, s1.iq, mode='full')))

    fig_hist, ax_hist = plt.subplots(1, 1)
    ax_hist.hist(np.real(s1_noisy), bins=100)
    plt.show()

    # seaborn pairgrid
    import seaborn as sns
    import pandas as pd
    print(s1.iq.shape)
    data = np.asarray([np.real(s1_noisy), np.imag(s1_noisy), np.real(s1.iq), np.imag(s1.iq)]).T
    print(np.shape(data))
    print(np.shape(data[0]))
    df = pd.DataFrame(data, columns=["I1", "Q1", "I2", "Q2"])
    g = sns.PairGrid(df, diag_sharey=False)
    g.map_diag(sns.histplot, bins=100)
    g.map_lower(sns.histplot, bins=100)
    g.map_upper(sns.histplot, bins=100)

    g.fig.suptitle("PairGrid")

    fig, ax = plt.subplots(1, 1)
    plot_complex_distribution(s1_noisy, ax=ax)

    pair_plot_complex_signals(s1_noisy, s1.iq)

    fig, ax = plt.subplots(1, 1)
    var = np.var(s1_noisy)
    plot_moment(s1_noisy, p=1, q=1, ax=ax, window_len=128)
    ax.plot([0, len(s1_noisy)], [var, var], color="red", linestyle="--")


    fig, ax = plt.subplots(1, 1)
    var = np.var(s1_noisy)
    plot_cross_moment(s1_noisy, s1.iq, px=1, qx=1, py=1, qy=1, ax=ax, window_len=32)
    #ax.plot([0, len(s1_noisy)], [var, var], color="red", linestyle="--")

    plt.show()
