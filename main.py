from views.windows.SignalAnalyzer.Overview import overview
from PyQt5.QtCore import pyqtSignal
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.colors import Normalize

from views.windows.run_window_as_app import *
from PyQt5.QtWidgets import QWidget, QComboBox, QHBoxLayout, QVBoxLayout

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.colorbar
from matplotlib.cm import ScalarMappable
from mpl.dsp.signal_plotter import *
from mpl.axis_config import *
from mpl.dsp.stat_plotters.complex_distrobution import plot_complex_distribution

if __name__ == "__main__":
    from tests.test_cases.new_basic_test_case import test_case_0
    from itertools import chain
    from core.dsp.signal_new import Signal
    from core.dsp.signal_analyzer.signal_analyzer import SignalAnalyzer
    from typing import Optional

    input_sigs, mixed_sigs, antenna = test_case_0()
    names: list[tuple[int, str]] = []
    sig_dict: dict[int, tuple[str, Signal]] = {}
    for idx, sig in enumerate(chain(input_sigs, mixed_sigs)):
        sig_dict[idx] = (sig.label, sig)
        names.append((idx, sig.label))

    def handle_event_selection(signal_id:int , event_id: int):
        print(f"Controller signal selection: {signal_id}")
        print(f"Controller event selection: {event_id}")
        (name, sig) = sig_dict[signal_id]
        event = sig.events[event_id]

        b = event.start_idx
        e = event.end_idx
        S, ex = SignalAnalyzer.STFT(x=sig.iq[b:e], fs=sig.fs)
        (tstart, tstop, f_low, f_high) = ex
        ex_tshift = (tstart+event.start_time, tstop+event.start_time, f_low, f_high)

        xcorr, lags = SignalAnalyzer.xcorr(sig.iq, event.pulse_iq, max_lag=int((e-b)/2))

        F, f = SignalAnalyzer.FFT(x=sig.iq[b:e]), SignalAnalyzer.fft_freqs(x=sig.iq[b:e], fs=sig.fs)
        P = SignalAnalyzer.phase(x=sig.iq[b:e])
        ovr.update_plots(x_vector=sig.iq[b:e], t_vector=sig.time_vector[b:e], phase_vector=P,
                         F=F,freqs=f,
                         Spec=20*np.log10(np.abs(S)), extent=ex_tshift,
                         xcorr=xcorr)

    def handle_selection(signal_id:int, event_id: Optional[int] = None):
        print(f"Controller: Selection -> Signal ID: {signal_id}, Event ID: {event_id}")
        _, sig = sig_dict[signal_id]
        t_total = sig.time_vector
        iq_total = sig.iq
        event_start = None
        event_end = None
        if event_id is None:
            e_names = [(idx, e.label) for idx, e in enumerate(sig.events)]
            ovr.populate_events(e_names)

            iq_slice = iq_total
            t_slice = t_total
            time_offset = 0.0
            xcorr = None
        else:
            event = sig.events[event_id]
            b, e = event.start_idx, event.end_idx

            iq_slice = sig.iq[b:e]
            t_slice = sig.time_vector[b:e]
            time_offset = event.start_time

            # Calculate cross-correlation only for events
            xcorr = np.abs(SignalAnalyzer.matched_filter(iq_total, event.pulse_iq))
            event_start = event.start_idx
            event_end = event.end_idx

        S, ex = SignalAnalyzer.STFT(x=iq_slice, fs=sig.fs)
        tstart, tstop, f_low, f_high = ex
        ex_shifted = (tstart + time_offset, tstop + time_offset, f_low, f_high)

        F, f = SignalAnalyzer.FFT(x=iq_slice), SignalAnalyzer.fft_freqs(x=iq_slice, fs=sig.fs)
        P = SignalAnalyzer.phase(x=iq_slice)

        ovr.update_plots(x_vector=iq_total,
                         x_vector_short = iq_slice,
                         t_vector=t_total,
                         t_vector_short=t_slice,
                         phase_vector=P,
                         F=20*np.log10(np.abs(F)), freqs=f,
                         Spec=20*np.log10(np.abs(S)), extent=ex_shifted,
                         xcorr=xcorr,
                         event_start=event_start,
                         event_end=event_end)




    def handle_signal_selection(signal_id: int):
        print(f"Controller signal selection: {signal_id}")
        # get signal
        (name, sig) = sig_dict[signal_id]

        # get all event names
        e_names = []
        for idx, e in enumerate(sig.events):
            e_names.append((idx,e.label))

        ovr.populate_events(e_names)

        S, ex = SignalAnalyzer.STFT(x=sig.iq, fs=sig.fs)
        F, f = SignalAnalyzer.FFT(x=sig.iq), SignalAnalyzer.fft_freqs(x=sig.iq, fs=sig.fs)
        P = SignalAnalyzer.phase(x=sig.iq)


        ovr.update_plots(x_vector=sig.iq, t_vector=sig.time_vector, phase_vector=P,
                         F=20*np.log10(np.abs(F)),freqs=f,
                         Spec=20*np.log10(np.abs(S)), extent=ex)
        pass



    app=create_app()

    ovr = overview()
    ovr.populate_dropdown(names)
    ovr.signal_selected.connect(lambda sig_id: handle_selection(sig_id, event_id=None))
    ovr.event_selected.connect(handle_selection)
    run_window_as_app(win=ovr)