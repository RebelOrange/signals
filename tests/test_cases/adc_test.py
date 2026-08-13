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
from tests.test_cases.mlms import multiple_jammer_case_0

def moving_average(
    x: np.ndarray,
    window_size: int = 51,
) -> np.ndarray:
    pwr = x
    kernel = np.ones(window_size) / float(window_size)
    avg_pwr = np.convolve(pwr, kernel, mode="same")

    return avg_pwr

def multiple_jammer_case_with_adc(
        tgt_on:bool = True,
    jam_SNRs:list[float] = [15, 30, 5, 0, -3],
    target_SNR:float = 3,
    num_jammers:int = 1,
    num_antenna_elements:int = 8,
    doas:list[float] = [15.0, -26.0, 33.0],
    sidelobe_gain_offset = 0,
    min_gate_range_jammer:list[float] = [0.1, 0.1],
    max_gate_range_jammer:list[float] = [0.9, 0.9],
jam_bw_range:list[float] = [0.5, 0.5],
    disconnected_elements:list[int] = []):

    input_sigs, rx_sigs, antenna = multiple_jammer_case_0(tgt_on=tgt_on,
                                                          tgt_SNR=target_SNR,
                                                             num_jammers=num_jammers,
                                                             num_antenna_elements=num_antenna_elements,
                                                          jam_doas = doas,
                                                          sidelobe_gain_offset=sidelobe_gain_offset,
                                                            min_gate_range_jammer =min_gate_range_jammer,
                                                            max_gate_range_jammer = max_gate_range_jammer,
                                                          bw_range_jammer=jam_bw_range,
                                                             jam_SNRs=jam_SNRs,
                                                          disconnected_elements =disconnected_elements)

    adc = ADC(ktb_db_int16=15, bits=14)
    adc_sigs = adc.process(rx_sigs, ktb_var=antenna.ktb_var)

    return input_sigs, adc_sigs, antenna, adc


def calculate_leaky_gamma(
        noise_bits: float,
        jnr_min_db: float,
        margin_db: float = 10.0,
        full_scale_bits: int = None
) -> float:
    """
    Calculates the Leaky LMS gamma parameter based on ADC noise floor and min JNR.

    Args:
        noise_bits: Number of LSB bits occupied by the ADC noise floor (X bits).
        jnr_min_db: Minimum JNR (in dB) that the algorithm should cancel.
        margin_db: Safety margin in dB below min jammer power (default: 10 dB).
        full_scale_bits: Total ADC bits if working with normalized float [-1, 1]. None for LSB counts.

    Returns:
        gamma: Linear leakage factor for Leaky LMS.
    """
    # Noise floor power in LSB^2
    sigma_n_sq = 2.0 ** (2.0 * noise_bits)

    # If using normalized IQ data in range [-1.0, 1.0]
    if full_scale_bits is not None:
        full_scale_power = (2.0 ** (full_scale_bits - 1)) ** 2
        sigma_n_sq = sigma_n_sq / full_scale_power

    # Calculate gamma sitting 'margin_db' below the minimum jammer power
    gamma_db = 10.0 * np.log10(sigma_n_sq) + jnr_min_db - margin_db
    gamma = 10.0 ** (gamma_db / 10.0)

    # Ensure gamma doesn't drop below the actual noise floor
    return max(gamma, sigma_n_sq)

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
    jam_SNRs = [0, 10, 5, 0, -3]
    target_SNR = 3
    num_jammers = 1
    num_antenna_elements = 8
    doas = [15.0, -26.0, 33.0]
    sidelobe_gain_offset = 0 #db
    input_sigs, adc_sigs, antenna, adc = multiple_jammer_case_with_adc(tgt_on=True,
                                                          target_SNR=target_SNR,
                                                             num_jammers=num_jammers,
                                                             num_antenna_elements=num_antenna_elements,
                                                          doas = doas,
                                                          sidelobe_gain_offset=sidelobe_gain_offset,
                                                          gate_range_jammer=[0.25, 0.3],
                                                             jam_SNRs=jam_SNRs,
                                                                 disconnected_elements=[])
    stop_time = time.time()

    print(len(adc_sigs))
    sig = adc_sigs[0]

    if False:
        fig, ax = plt.subplots()
        plot_iq_timeseries(iq=20*np.log10(np.abs(sig.iq)), t=sig.t, ax=ax)
        plot_iq_timeseries(iq=moving_average(20*np.log10(np.abs(sig.iq))), t=sig.t, ax=ax)

        plt.show()


