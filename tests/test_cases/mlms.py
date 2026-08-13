import random

import numpy as np

from core.antennas.array import ElementPatterns
from core.antennas.classic.ULA import ULA
from core.dsp.signal_new import Signal
from core.dsp.mixer import Mixer
from core.dsp.signal_generators.sig_gen_new import SignalGenerator
from core.dsp.datatypes import PulsedSignalConfig, TimeGate, TimeGrid
from core.dsp.signal_generators.signal_providers.FM import LFMConfig
from core.dsp.signal_generators.signal_providers.Noise import NoiseConfig


def multiple_jammer_case_0(tgt_type: str = "lfm",
                           tgt_on: bool = True,
                           num_jammers:int = 3,
                           num_antenna_elements: int = 8,
                           jam_SNRs: list[float] = None,
                           jam_doas: list[float] = None,
                           TIMEIT: bool = False,
                           ) -> tuple[list[Signal], list[Signal], ULA]:
    ## Simulation config
    # antenna
    num_elements = num_antenna_elements

    # signal setup
    JS = 30
    fs = 10e6
    total_samps = 5000

    tgt_type = tgt_type.lower()
    tgt_doa = (0.0, 0.0)  # degrees
    tgt_bw = 0.01 * fs  # for lfm
    tgt_start_samp = 1000
    tgt_min_num_samps = 2000
    SNR = 10
    sig_amp = 1
    ktb_var = sig_amp / 10

    #jam_doa = (jam_az, 0.0)  # degrees
    noise_bw = 0.5 * fs
    noise_start_samp = 500
    noise_min_num_samps = 3000

    # class instantiation
    antenna = ULA(num_elements=num_elements)
    patterns = ([ElementPatterns.taylor_subarray(num_sub_elements=20)]
                + [ElementPatterns.delta_subarray(4)] * (num_antenna_elements-1))
    antenna.set_patterns(patterns)

    ################# baseline signals: jammer + tgt signals
    t_grid = TimeGrid(sample_rate=fs, duration=1000e-6)
    wfm_config = LFMConfig(chirp_bandwidth=tgt_bw,
                          amplitude=sig_amp,
                          frequency_center=0,
                          pulse_width=500e-6)
    tgt_sig_config = PulsedSignalConfig(waveform_config=wfm_config,
                                        gate=TimeGate(start_time=200e-6, stop_time=700e-6))

    if TIMEIT:
        import time
        start_time = time.time()
    sigs = []
    sigGen = SignalGenerator(time_grid=t_grid)
    tgt_sig = sigGen.create_pulsed_signal([tgt_sig_config], label="Pulsed LFM")
    doas = []
    if tgt_on:
        sigs.append(tgt_sig)
        doas.append(tgt_doa)

    # generate 7 random jammer configs
    confs = []
    jam_sigs = []
    jam_vars = []
    for i in range(num_jammers):
        noise_bw = random.uniform(0.89*fs, 0.89*fs)
        freq_center = random.uniform(-0.0*fs, 0.0*fs)
        if jam_SNRs is None:
            jam_SNR = random.uniform(-3, 30)+30
        else:
            jam_SNR = jam_SNRs[i] + 30
        jam_var = 10 ** (jam_SNR/ 10) * sig_amp
        jam_vars.append(jam_var)
        start_time = random.uniform(0e-6, 0e-6)
        stop_time = random.uniform(1000e-6, 1000e-6)

        conf = PulsedSignalConfig(waveform_config=NoiseConfig(bandwidth=noise_bw,
                                                              frequency_center=freq_center,
                                                              variance=jam_var),
                                  gate=TimeGate(start_time=start_time, stop_time=stop_time))
        confs.append(conf)
        jam_sigs.append(sigGen.create_pulsed_signal([conf],label=f"Jammer {i}"))
    print(f"number of confs: {len(confs)}")
    print(f"Min Jam Variance: {np.min(jam_vars)*0.001} ({10*np.log10(np.min(jam_vars))-30})")
    print(f"Max Jam Variance: {np.max(jam_vars)*0.001} ({10*np.log10(np.max(jam_vars))-30})")
    print(f"kTB variance: {ktb_var} ({10*np.log10(ktb_var)})")


    input_sigs = sigs + jam_sigs

    if TIMEIT:
        stop_time = time.time()
        print(f"\nSignal generation time: {stop_time - start_time}\n")

    print(f"Number of input sigs: {len(input_sigs)}")
    ktb_config = tgt_sig_config

    # add channel ktB noise
    antenna.set_ktb_variance(ktb_var)
    antenna.mixer = Mixer()

    ################ recieve signals with DOAs ################
    # X = antenna.receive([tgt_sig.iq, jam_sig.iq], [tgt_doa, jam_doa]) # data matrix method


    def random_exclusive_float(range1, range2):
        """
        Generates a uniform float from either range1 [min, max] or range2 [min, max].
        Accounts for range widths to maintain true uniform probability.
        """
        # 1. Calculate the span/width of each valid window
        width1 = range1[1] - range1[0]
        width2 = range2[1] - range2[0]
        total_width = width1 + width2

        # 2. Pick a range based on its proportional size (weight)
        chosen_range = random.choices([range1, range2], weights=[width1, width2])[0]

        # 3. Sample uniformly from the selected range
        return random.uniform(chosen_range[0], chosen_range[1])

    for i in range(num_jammers):
        az = random_exclusive_float([-65, -10], [10, 65])
        if jam_doas is None:
            doas.append((az, 0.0))
        else:
            doas.append((jam_doas[i],0.0))
    if TIMEIT:
        start_time = time.time()
    rx_sigs: list[Signal] = antenna.receive(input_sigs, doas, ktb_var=ktb_var)

    if TIMEIT:
        stop_time = time.time()
        print(f"\nSignal receiving time: {stop_time - start_time}\n")

    return input_sigs, rx_sigs, antenna

def compute_simulation_gamma(
    M: int,
    K: int,
    var_jam_min: float,
    var_jam_max: float,
    var_noise: float,
    target_residual: str = "noise_floor",  # 'noise_floor' or 'db_suppression'
    suppression_db: float = 30.0,
    dtype=np.float32,
) -> float:
    """Calculates optimal gamma for Leaky NLMS/LMS in floating-point simulation.

    Parameters:
    - M: Number of auxiliary channels
    - K: Number of FIR delay taps
    - var_jam_min: Variance (power) of weakest jammer
    - var_jam_max: Variance (power) of strongest jammer
    - var_noise: Variance of thermal noise floor
    - target_residual: 'noise_floor' or 'db_suppression'
    - suppression_db: Target suppression in dB (if target_residual='db_suppression')
    - dtype: np.float32 or np.float64
    """
    N = M * K
    lambda_min = N * var_jam_min + var_noise
    lambda_max = N * var_jam_max + var_noise

    # Machine precision epsilon
    eps_mach = np.finfo(dtype).eps

    # 1. Calculate Theoretical Gamma
    if target_residual == "noise_floor":
        P_res = var_noise
        if var_jam_min <= var_noise:
            # Jammer is already at/below noise floor
            gamma_theory = lambda_min
        else:
            A = np.sqrt(P_res) / np.sqrt(var_jam_min)
            gamma_theory = (A / (1.0 - A)) * lambda_min
    elif target_residual == "db_suppression":
        A = 10.0 ** (-abs(suppression_db) / 20.0)
        gamma_theory = (A / (1.0 - A)) * lambda_min
    else:
        raise ValueError("Invalid target_residual option.")

    # 2. Enforce Numerical Floating-Point Bounds
    gamma_floor = eps_mach * lambda_max * 10.0  # 10x safety margin above eps
    gamma_ceiling = 0.5 * lambda_min  # Keep well below lambda_min

    # Clamp gamma within valid numerical range
    gamma_sim = np.clip(gamma_theory, gamma_floor, gamma_ceiling)

    return float(gamma_sim)

if __name__ == "__main__":

    import matplotlib.pyplot as plt
    from mpl.antenna_plotter import plot_scan_response, plot_element_scan_responses
    from mpl.dsp.signal_plotter import plot_iq_timeseries, plot_event_window, plot_spectrogram
    import time
    import matplotlib
    from core.dsp.algorithms.block_algorithms.block_processor import BlockProcessor
    from core.dsp.algorithms.block_algorithms.providers.MVDR import MvdrConfig
    from core.dsp.signal_analyzer.signal_analyzer import SignalAnalyzer
    from core.dsp.algorithms.canceller_algorithms.providers.LMS import nlms
    from core.dsp.algorithms.canceller_algorithms.providers.Wiener import Wiener

    matplotlib.use("Qt5Agg")

    start_time = time.time()
    jam_SNRs = [30, 10, 5, 0, -3]
    num_jammers = 3
    num_antenna_elements = 8
    doas = [15.0, -26.0, 33.0]
    input_sigs, rx_sigs, antenna = multiple_jammer_case_0(tgt_on=True,
                                                             num_jammers=num_jammers,
                                                             num_antenna_elements=num_antenna_elements,
                                                          jam_doas = doas,
                                                             jam_SNRs=jam_SNRs)
    stop_time = time.time()

    doas = antenna.doas

    X = antenna.X_n

    # Extract dynamic power parameters from antenna and generated signals
    M_aux = X.shape[0] - 1  # 7 auxiliary channels
    K_taps = 2  # FIR order
    var_noise = antenna.ktb_var  # Thermal noise floor

    # Estimate actual jammer power bounds from signal matrices
    X_aux = X[1:, :]
    R_xx = X_aux@X_aux.conj().T
    print(f"Rank: {np.linalg.matrix_rank(R_xx)}")
    ch_powers = np.mean(np.abs(X_aux) ** 2, axis=1)
    var_jam_min = np.min(ch_powers)
    var_jam_max = np.max(ch_powers)

    # Calculate optimal simulation gamma using dynamic signal parameters
    gamma = compute_simulation_gamma(
        M=M_aux,
        K=K_taps,
        var_jam_min=var_jam_min,
        var_jam_max=var_jam_max,
        var_noise=var_noise,
        target_residual="noise_floor",
        dtype=np.float64,
    )

    print(f"Calculated Leaky LMS gamma: {gamma:.4e}")

    lms = nlms(X=X[1:,:], d=X[0,:], mu=1.0, order=K_taps, gamma=gamma)
    wien = Wiener(X=X[1:,:], d=X[0,:], order=3)
    main_resp, _, _ = lms.run()


    processor = BlockProcessor.from_config(config=MvdrConfig())
    Y = processor.process_datamatrix(X, antenna.manifold_vector((0.0, 0.0)), np.array([]))
    sig = Signal(iq=Y, sample_rate=rx_sigs[0].sample_rate, label="beamformed Output")

    print(f"output shape: {Y.shape}")
    print(f" weight shape: {processor.W.shape}")
    antenna.set_weights(processor.W)

    fig, ax = plt.subplots()
    x, y = antenna.scan_response()
    plot_scan_response(y, x, ax=ax)
    x, y = antenna.scan_response_weights()
    plot_scan_response(y, x, ax=ax)
    lims = [-50, 20]
    ax.set_ylim((lims[0], lims[1]))
    for i in range(num_jammers+1):
        if i ==0:
            ax.plot([doas[i][0], doas[i][0]],lims, "--g")
        else:
            ax.plot([doas[i][0], doas[i][0]],lims, "--r")


    fig, ax1 = plt.subplots(2,1)
    plot_iq_timeseries(rx_sigs[0].time_vector, iq=np.squeeze(Y), ax=ax1[0])
    plot_iq_timeseries(rx_sigs[0].time_vector, iq=main_resp, ax=ax1[1])





    fig, ax3 = plt.subplots()
    x, y = antenna.element_scan_responses()
    plot_element_scan_responses(az_grid=x, element_powers=y, ax=ax3)
    lims = [-50, 20]
    ax3.set_ylim((lims[0], lims[1]))
    print(len(doas))
    for i in range(num_jammers+1):
        if i ==0:
            ax3.plot([doas[i][0], doas[i][0]],lims, "--g")
        else:
            ax3.plot([doas[i][0], doas[i][0]],lims, "--r")


    # beam former
    S, extent = SignalAnalyzer.STFT(np.squeeze(Y), rx_sigs[0].sample_rate)
    fig, ax2 = plt.subplots()
    plot_spectrogram(S=S, extent=extent, ax=ax2)
    # LMS
    S_n, extent_n = SignalAnalyzer.STFT(np.squeeze(main_resp), rx_sigs[0].sample_rate)
    fig, ax8 = plt.subplots()
    plot_spectrogram(S=S_n, extent=extent_n, ax=ax8)
    # original
    S_n, extent_n = SignalAnalyzer.STFT(np.squeeze(X[0, :]), rx_sigs[0].sample_rate)
    fig, ax9 = plt.subplots()
    plot_spectrogram(S=S_n, extent=extent_n, ax=ax9)
    # sig.save_to_csv(file_path="./test.csv")

    plt.show()
    if False:
        print(f"\n attempting to plot signal with {sig.num_samples} samples, "
              f"samplerate: {sig.sample_rate},"
              f" duration: {sig.duration}\n,"
              f" Ts: {sig.dT} "
              f"and a timevector with {len(sig.t)} samples")
        plot_iq_timeseries(iq=sig.iq, t=sig.t, ax=ax[1])
        event_idx = 0
        plot_event_window(t=sig.t, ax=ax[1],
                          end_idx=sig.events[event_idx].end_idx,
                          start_idx=sig.events[event_idx].start_idx,
                          name=sig.events[event_idx].label)
        event_idx = 1
        plot_event_window(t=sig.t, ax=ax[1],
                          end_idx=sig.events[event_idx].end_idx,
                          start_idx=sig.events[event_idx].start_idx,
                          name=sig.events[event_idx].label)

        plt.show()
