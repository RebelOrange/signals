import numpy as np
from matplotlib import pyplot as plt

from core.antennas.classic.ULA import ULA
from core.dsp.iq_signal import Signal
from core.dsp.mixer import Mixer
from core.dsp.signal_generators.sig_gen import SignalGenerator, SignalConfig

from mpl.dsp.signal_plotter import *
from mpl.antenna_plotter import *

import matplotlib
#matplotlib.use("Qt5Agg")

if __name__ == "__main__":
    ## Simulation config
    # antenna
    num_elements = 20

    # signal setup
    JS = 6
    fs = 10e3
    total_samps = 5000

    tgt_type = "lfm"
    tgt_doa = (0.0, 0.0) # degrees
    tgt_bw = 0.1*fs # for lfm
    tgt_start_samp = 1000
    tgt_min_num_samps = 2000
    SNR = 10
    sig_amp = 1
    ktb_var = sig_amp/10**(SNR/10)

    jam_doa = (0.5, 0.0) # degrees
    noise_bw = 0.2*fs
    noise_start_samp = 500
    noise_min_num_samps = 3000

    # class instantiation
    sig_gen = SignalGenerator()
    antenna = ULA(num_elements=num_elements)

    ################# baseline signals: jammer + tgt signals
    tgt_sig_config = SignalConfig(sample_rate=fs,
                                      lfm_f_lower=-tgt_bw/2,
                                      lfm_f_upper=tgt_bw/2,
                                      amplitude=1,
                                  SNR=SNR,
                                      min_num_samples=tgt_min_num_samps,
                                  mask_type="sample",
                                      start_sample=tgt_start_samp,
                                      total_samples=total_samps,
                                  bpsk_code=sig_gen.barker_code(order=13))
    match tgt_type:
        case "lfm":
            tgt_sig:Signal = sig_gen.generate_LFM(config=tgt_sig_config)
        case "bpsk":
            tgt_sig:Signal = sig_gen.generate_BPSK(config=tgt_sig_config)
    jam_var = 10**(JS/10)*tgt_sig.variance

    jam_sig_config = SignalConfig(sample_rate=fs,
                                  noise_f_lower=-noise_bw/2,
                                  noise_f_upper=noise_bw/2,
                                  noise_var=jam_var,
                                  mask_type="sample",
                                  min_num_samples=noise_min_num_samps,
                                  start_sample=noise_start_samp,
                                  total_samples=total_samps,
                                  )
    jam_sig = sig_gen.generate_Noise(config=jam_sig_config)

    ktb_config = tgt_sig_config

    # add channel ktB noise
    antenna.set_ktb_variance(ktb_var)
    antenna.mixer = Mixer()

    ################ recieve signals with DOAs ################
    #X = antenna.receive([tgt_sig.iq, jam_sig.iq], [tgt_doa, jam_doa]) # data matrix method
    rx_sigs:list[Signal] = antenna.receive([tgt_sig, jam_sig], [tgt_doa, jam_doa])
    #print(X.shape)
    print(len(rx_sigs))
    antenna.beamform(steering_doa=(0.0,0.0))

    ################ figures #######################
    # antenna
    fig, ax = plt.subplots()
    x, y = antenna.scan_response()
    plot_scan_response(resp=y, az_points=x, ax=ax)

    # timeseries and mixing process



    plt.show()
    pass