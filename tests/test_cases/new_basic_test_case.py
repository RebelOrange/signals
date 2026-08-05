import numpy as np

from core.antennas.classic.ULA import ULA
from core.dsp.signal_new import Signal
from core.dsp.mixer import Mixer
from core.dsp.signal_generators.sig_gen_new import SignalGenerator
from core.dsp.datatypes import PulsedSignalConfig, TimeGate, TimeGrid
from core.dsp.signal_generators.signal_providers.FM import LFMConfig
from core.dsp.signal_generators.signal_providers.Noise import NoiseConfig

def test_case_0(tgt_type:str = "lfm",
                tgt_az:float = 0.0,
                jam_az:float = 10.0,
                TIMEIT:bool = False,
                ) -> tuple[list[Signal], list[Signal], ULA]:
    ## Simulation config
    # antenna
    num_elements = 20

    # signal setup
    JS = -20
    fs = 10e6
    total_samps = 5000

    tgt_type = tgt_type.lower()
    tgt_doa = (tgt_az, 0.0)  # degrees
    tgt_bw = 0.2 * fs  # for lfm
    tgt_start_samp = 1000
    tgt_min_num_samps = 2000
    SNR = 10
    sig_amp = 1
    ktb_var = sig_amp / 10

    jam_doa = (jam_az, 0.0)  # degrees
    noise_bw = 0.5* fs
    noise_start_samp = 500
    noise_min_num_samps = 3000
    
    # class instantiation
    antenna = ULA(num_elements=num_elements)

    ################# baseline signals: jammer + tgt signals
    t_grid = TimeGrid(sample_rate=fs,duration=1000e-6)
    tgt_sig_config = PulsedSignalConfig(waveform_config=LFMConfig(chirp_bandwidth=tgt_bw,
                                                                  amplitude=sig_amp,
                                                                  frequency_center=0,
                                                                  pulse_width=500e-6),
                                        gate=TimeGate(start_time=200e-6, stop_time=700e-6))
    jam_var = 10 ** (JS / 10) * sig_amp
    jam_sig_config = PulsedSignalConfig(waveform_config=NoiseConfig(bandwidth=noise_bw,
                                                                    frequency_center=0,
                                                                    variance=jam_var,
                                                                    ),
                                        gate=TimeGate(start_time=200e-6, stop_time=600e-6))

    """
    tgt_sig_config = SignalConfig(sample_rate=fs,
                                  lfm_f_lower=-tgt_bw / 2,
                                  lfm_f_upper=tgt_bw / 2,
                                  amplitude=1,
                                  SNR=SNR,
                                  min_num_samples=tgt_min_num_samps,
                                  mask_type="sample",
                                  start_sample=tgt_start_samp,
                                  total_samples=total_samps,
                                  bpsk_code=sig_gen.barker_code(order=13))
    match tgt_type:
        case "lfm":
            tgt_sig: Signal = sig_gen.generate_LFM(config=tgt_sig_config)
        case "bpsk":
            tgt_sig: Signal = sig_gen.generate_BPSK(config=tgt_sig_config)

    jam_sig_config = SignalConfig(sample_rate=fs,
                                  noise_f_lower=-noise_bw / 2,
                                  noise_f_upper=noise_bw / 2,
                                  noise_var=jam_var,
                                  mask_type="sample",
                                  min_num_samples=noise_min_num_samps,
                                  start_sample=noise_start_samp,
                                  total_samples=total_samps,
                                  )
    jam_sig = sig_gen.generate_Noise(config=jam_sig_config)
    """
    if TIMEIT:
        import time
        start_time = time.time()
    sigGen = SignalGenerator(time_grid=t_grid)
    tgt_sig = sigGen.create_pulsed_signal([tgt_sig_config], label="Pulsed LFM")
    jam_sig = sigGen.create_pulsed_signal([jam_sig_config], label="Pulsed Jammer")
    if TIMEIT:
        stop_time = time.time()
        print(f"\nSignal generation time: {stop_time - start_time}\n")
    input_sigs = [tgt_sig, jam_sig]

    ktb_config = tgt_sig_config

    # add channel ktB noise
    antenna.set_ktb_variance(ktb_var)
    antenna.mixer = Mixer()

    ################ recieve signals with DOAs ################
    # X = antenna.receive([tgt_sig.iq, jam_sig.iq], [tgt_doa, jam_doa]) # data matrix method
    if TIMEIT:
        start_time = time.time()
    rx_sigs: list[Signal] = antenna.receive(input_sigs, [tgt_doa, jam_doa], ktb_var=ktb_var)

    if TIMEIT:
        stop_time = time.time()
        print(f"\nSignal receiving time: {stop_time - start_time}\n")


    return input_sigs, rx_sigs, antenna

if __name__ == "__main__":

    import matplotlib.pyplot as plt
    from mpl.antenna_plotter import plot_scan_response
    from mpl.dsp.signal_plotter import plot_iq_timeseries, plot_event_window
    import time
    import matplotlib
    matplotlib.use("Qt5Agg")

    start_time = time.time()
    input_sigs, rx_sigs, antenna = test_case_0(TIMEIT=True)
    stop_time = time.time()
    print(f"\nTest case time: {stop_time - start_time}\n")

    fig, ax = plt.subplots(2,1, constrained_layout=True)
    start_time = time.time()
    points, resp = antenna.scan_response()
    stop_time = time.time()
    print(f"\nScan response calculation time: {stop_time - start_time}\n")
    plot_scan_response(resp=resp, az_points=points, ax=ax[0])

    sig = rx_sigs[0]
    sig.save_to_csv(file_path="./test.csv")

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
        event_idx =1
        plot_event_window(t=sig.t, ax=ax[1],
                          end_idx=sig.events[event_idx].end_idx,
                          start_idx=sig.events[event_idx].start_idx,
                          name=sig.events[event_idx].label)

        plt.show()
