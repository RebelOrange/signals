import matplotlib.pyplot as plt
from core.dsp.signal_generators.sig_gen import SignalGenerator, SignalConfig
from mpl.dsp.signal_plotter import *
from core.dsp.iq_signal import Signal
from mpl.dsp.stat_plotters.pair_plotter import pair_plot_complex_signals
from mpl.dsp.stat_plotters.moment_plotter import plot_moment

from mpl.dsp.stat_plotters.cum_plot import plot_auto_cumulant_4th


if __name__ == "__main__":

    sigGen = SignalGenerator()
    config_lfm = SignalConfig(sample_rate=10e3,
                              lfm_f_lower=-1000,
                              lfm_f_upper=1000,
                              amplitude=1,
                              SNR=10,
                              min_num_samples=1000,
                              mask_type="sample",
                              start_sample=1500,
                              stop_sample=2500,
                              total_samples=3000
                              )


    config_bpsk = SignalConfig(sample_rate=10e3,
                              amplitude=1,
                               phase_offset=45,
                              SNR=10,
                              min_num_samples=1000,
                              mask_type="sample",
                              start_sample=1200,
                              stop_sample=2500,
                              total_samples=3000,
                               bpsk_code=sigGen.barker_code(order=13)
                              )

    des_sig: Signal = sigGen.generate_LFM(config=config_lfm)
    des_sig: Signal = sigGen.generate_BPSK(config=config_bpsk)
    # calculate desired variance for -6dB J2S
    J2S = 3
    req_var = 10**(J2S/10)*des_sig.variance

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
    ktb_sig: Signal = sigGen.generate_system_noise(config = config_lfm)
    rx_sig = des_sig + jamming_sig + ktb_sig

    pair_plot_complex_signals(rx_sig.iq, des_sig.iq)

    fig, ax = plt.subplots(1, 1)
    plot_moment(rx_sig.iq, 2, 2, ax=ax)

    fig, ax = plt.subplots(1, 2)
    S, ex = rx_sig.STFT()
    plot_spectrogram(S, ex, ax=ax[0])
    plot_iq_timeseries(rx_sig.sample_vector, rx_sig.iq, ax=ax[1])

    fig, ax = plt.subplots(2, 1)
    ax_config = AxisConfig(title="My Cumulant", xlabel="", ylabel="", grid=True, legend=False)
    plot_auto_cumulant_4th(rx_sig.iq, ax=ax[0], window_len=128, type=0, config=ax_config)
    ax_config = AxisConfig(title="Gem Cumulant", xlabel="", ylabel="", grid=True, legend=False)
    plot_auto_cumulant_4th(rx_sig.iq, ax=ax[1], window_len=128, type=1, config=ax_config)

    plt.show()