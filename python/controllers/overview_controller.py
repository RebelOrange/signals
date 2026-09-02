from controllers import AppState
from views.windows.SignalAnalyzer.Overview import overview
from views.windows.init_view.ConfigDialog import DynamicConfigDialog
from core.antennas.array import ElementPatterns, AntennaArray
from core.antennas.classic.ULA import ULA
from core.dsp.signal_new import Signal
from core.dsp.signal_generators.sig_gen_new import SignalGenerator
from core.dsp.signal_analyzer.signal_analyzer import SignalAnalyzer

import numpy as np
from .AppState import AppState
from typing import Optional
from itertools import chain

class SignalOverviewController:

    def __init__(self, view: overview, state: AppState):
        self.view = view
        self.state = state
        self.names: list[tuple[int, str]] = []
        self.sig_dict: dict[int, tuple[str, Signal]] = {}

        self._connect_signals()

    def _connect_signals(self):
        self.view.signal_selected.connect(lambda sig_id: self._handle_selection(sig_id, event_id=None))
        pass

    def update_view_from_state(self):
        print(self.state)
        for idx, sig in enumerate(chain(self.state.input_sigs, self.state.rx_sigs)):
            print(f"{idx}: {sig.label}")
            print(sig)
            self.sig_dict[idx] = (sig.label, sig)
            self.names.append((idx, sig.label))
        self.view.populate_dropdown(self.names)

    def _handle_selection(self, signal_id:int, event_id: Optional[int]=None):
        print(f"Controller: Selection -> Signal ID: {signal_id}, Event ID: {event_id}")
        _, sig = self.sig_dict[signal_id]
        t_total = sig.time_vector
        iq_total = sig.iq
        event_start = None
        event_end = None
        if event_id is None:
            e_names = [(idx, e.label) for idx, e in enumerate(sig.events)]
            self.view.populate_events(e_names)

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

        self.view.update_plots(x_vector=iq_total,
                         x_vector_short=iq_slice,
                         t_vector=t_total,
                         t_vector_short=t_slice,
                         phase_vector=P,
                         F=20 * np.log10(np.abs(F)), freqs=f,
                         Spec=20 * np.log10(np.abs(S)), extent=ex_shifted,
                         xcorr=xcorr,
                         event_start=event_start,
                         event_end=event_end)
        pass