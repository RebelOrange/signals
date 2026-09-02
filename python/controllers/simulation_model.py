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
from core.dsp.analog_to_digital.adc import ADC
from typing import Any
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

def sim_case_0(tgt_config: Any = LFMConfig,
                           tgt_on: bool = True,
                           tgt_SNR: float = 3,
                           num_jammers:int = 3,
                           num_antenna_elements: int = 8,
                           jam_SNRs: list[float] = None,
                           jam_doas: list[float] = None,
                           sidelobe_gain_offset:int=0,
                           sidelobe_gain_normalization:bool=True,
                           bw_range_jammer: list[float] = [0.5, 0.5],
                           min_gate_range_jammer: list[float] = [0.0, 0.0],
                           max_gate_range_jammer: list[float] = [1.0, 1.0],
                           disconnected_elements:list[int] = [],
                           TIMEIT: bool = False,
                           ):
    ## Simulation config
    # antenna
    num_elements = num_antenna_elements

    # signal setup
    JS = 30
    fs = 10e6
    total_samps = 5000

    tgt_doa = (0.0, 0.0)  # degrees
    tgt_bw = 0.01 * fs  # for lfm
    tgt_start_samp = 1000
    tgt_min_num_samps = 2000
    SNR = 10
    sig_amp = 1
    ktb_var = sig_amp / 10**(tgt_SNR/10)

    #jam_doa = (jam_az, 0.0)  # degrees
    noise_bw = 0.5 * fs
    noise_start_samp = 500
    noise_min_num_samps = 3000
    ssl_taylor = 20

    # class instantiation
    antenna = ULA(num_elements=num_elements)
    patterns = ([ElementPatterns.taylor_subarray(num_sub_elements=20, sll_db=ssl_taylor)]
                + [ElementPatterns.delta_subarray(4, gain_offset=(-ssl_taylor+3))] * (num_antenna_elements-1))
    antenna.set_disconnected_elements(disconnected_elements)
    antenna.set_patterns(patterns)

    main_pattern = antenna.element_patterns[0]

    ################# baseline signals: jammer + tgt signals
    t_grid = TimeGrid(sample_rate=fs, duration=1000e-6)
    wfm_config = tgt_config
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
    for i in range(num_jammers):
        az = random_exclusive_float([-65, -10], [10, 65])
        if jam_doas is None:
            doas.append((az, 0.0))
        else:
            doas.append((jam_doas[i],0.0))

    # generate 7 random jammer configs
    confs = []
    jam_sigs = []
    jam_vars = []
    for i in range(num_jammers):
        noise_bw = random.uniform(bw_range_jammer[0]*fs, bw_range_jammer[1]*fs)
        freq_center = random.uniform(-0.0*fs, 0.0*fs)
        sidelobe_gain = np.abs(main_pattern(jam_doas[i],0.0))**2
        print(f"using sidelobe gain {10*np.log10(1/sidelobe_gain)} at f{jam_doas[i]} az")
        if jam_SNRs is None:
            jam_SNR = random.uniform(-3, 30)+sidelobe_gain_offset+10*np.log10(1/sidelobe_gain)
        else:
            jam_SNR = jam_SNRs[i] +sidelobe_gain_offset+10*np.log10(1/sidelobe_gain)
        jam_var = 10 ** (jam_SNR/ 10) * sig_amp
        jam_vars.append(jam_var)
        start_time = random.uniform(min_gate_range_jammer[0]*t_grid.duration, min_gate_range_jammer[1]*t_grid.duration)
        stop_time = random.uniform(max_gate_range_jammer[0]*t_grid.duration, max_gate_range_jammer[1]*t_grid.duration)

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




    if TIMEIT:
        start_time = time.time()
    rx_sigs: list[Signal] = antenna.receive(input_sigs, doas, ktb_var=ktb_var)

    if TIMEIT:
        stop_time = time.time()
        print(f"\nSignal receiving time: {stop_time - start_time}\n")

    adc = ADC(ktb_db_int16=15, bits=14)
    adc_sigs = adc.process(rx_sigs, ktb_var=antenna.ktb_var)


    return input_sigs, rx_sigs, antenna, adc, adc_sigs