import numpy as np

from core.antennas.classic.ULA import ULA
from core.dsp.signal_new import Signal
from core.dsp.mixer import Mixer
from core.dsp.signal_generators.sig_gen_new import SignalGenerator
from core.dsp.datatypes import PulsedSignalConfig, TimeGate, TimeGrid
from core.dsp.signal_generators.signal_providers.FM import LFMConfig
from core.dsp.signal_generators.signal_providers.Noise import NoiseConfig
from core.dsp.signal_generators.signal_providers.PSK import BPSKConfig, CodeConstructer
from core.dsp.signal_generators.signal_providers.CW import CwConfig

if __name__ == "__main__":
    # params
    fs = 10e6
    num_elements=4
    sig_doa = (0.0, 0.0)
    sig_amp = 1
    j_doa_1 = (10.0, 0.0)
    j_doa_2 = (-20.0, 0.0)
    JS_1 = 10
    J_1_var = 10**(JS_1/10)*sig_amp
    JS_2 = 25
    J_2_var = 10**(JS_2/10)*sig_amp
    sig_bw = 0.25*fs
    noise_1_bw =0.35*fs
    noise_2_bw = 0.1*fs
    ktb_var = sig_amp/10

    ## signal configs
    cw_config = CwConfig(frequency=500e3, phase=30.0*np.pi/180)
    lfm_config = LFMConfig(chirp_bandwidth=sig_bw,
                                          amplitude=sig_amp,
                                          frequency_center=0,
                                          pulse_width=500e-6)
    bpsk_config = BPSKConfig(code=CodeConstructer.barker(order=13),
                             phase=-60*np.pi/180,
                             frequency=100e3)

    jam_1_config = NoiseConfig(bandwidth=noise_1_bw,
                               frequency_center=0,
                               variance=J_1_var)

    jam_2_config = NoiseConfig(bandwidth=noise_2_bw,
                               frequency_center=200e3,
                               variance=J_2_var)

    t_grid = TimeGrid(sample_rate=fs,duration=500e-6)

    ############### Test cases ###########################
    root_folder = "/opt/rfdev-envs/python/signals/tests/lillian_test_cases/"
    ############## single signals ##########
    # 1. CW
    if False:
        sigGen = SignalGenerator.from_config(time_grid=t_grid, signal_config=cw_config)
        sig = sigGen.generate_signal(ignore_events=True)
        sig.save_to_csv(root_folder+ "single_signals/pulse_1.csv")

        # 2. LFM
        sigGen = SignalGenerator.from_config(time_grid=t_grid, signal_config=lfm_config)
        sig = sigGen.generate_signal(ignore_events=True)
        sig.save_to_csv(root_folder + "single_signals/pulse_2.csv")

        # 3. BPSK
        sigGen = SignalGenerator.from_config(time_grid=t_grid, signal_config=bpsk_config)
        sig = sigGen.generate_signal(ignore_events=True)
        sig.save_to_csv(root_folder + "single_signals/pulse_3.csv")

        # 4. Noise
        sigGen = SignalGenerator.from_config(time_grid=t_grid, signal_config=jam_1_config)
        sig = sigGen.generate_signal(ignore_events=True)
        sig.save_to_csv(root_folder + "single_signals/pulse_4.csv")



    wfm_config = LFMConfig(chirp_bandwidth=500e3,
                          amplitude=1,
                          frequency_center=0,
                          pulse_width=500e-6)
    tgt_sig_config = PulsedSignalConfig(waveform_config=wfm_config,
                                        gate=TimeGate(start_time=200e-6, stop_time=700e-6))

    conf = PulsedSignalConfig(waveform_config=NoiseConfig(bandwidth=1e6,
                                                          frequency_center=0,
                                                          variance=5),
                              gate=TimeGate(start_time=0, stop_time=999e-6))

    t_grid = TimeGrid(sample_rate=fs, duration=1000e-6)
    sigGen = SignalGenerator(time_grid=t_grid)
    sig = sigGen.create_pulsed_signal(pulsed_configs=[tgt_sig_config, conf])
    sig.save_to_csv(root_folder+"examp.csv")





