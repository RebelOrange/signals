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

# Uses MVC, View should not contain any data objects
class overview(QWidget):
    """Displays an overview of a selected signal, from list of signals selected from a dropdown"""

    signal_selected = pyqtSignal(int)
    event_selected = pyqtSignal(int, int) #signal selected id and event id
    def __init__(self):
        super().__init__()

        # drop down selection for data selection
        self.dropdown = QComboBox()
        self.event_dropdown = QComboBox()
        self.figure:Figure = Figure(constrained_layout=True)
        self.axes:Axes
        self.canvas: FigureCanvas
        self.spectrogram_cbar = None

        self.setLayout(self._layout())

    def _init_ui(self):
        self._init_dropdown()
        self._init_event_dropdown()
        self._init_figure()

    def _init_dropdown(self):
        self.dropdown.addItem("Select a signal...", userData=None)
        self.dropdown.currentIndexChanged.connect(self._on_selection_change)

    def _init_event_dropdown(self):
        self.event_dropdown.addItem("Select an event...", userData=None)
        self.event_dropdown.currentIndexChanged.connect(self._on_event_change)

    def _init_figure(self):
        mosaic_layout = [["timeseries", "fft", "phase"],
                         ["xcorr", "spectrogram", "const"]]
        self.axes = self.figure.subplot_mosaic(mosaic_layout)
        for name, ax in self.axes.items():
            ax.set_title(name)
        self.canvas = FigureCanvas(self.figure)

    def _layout(self):
        self._init_ui()

        layout_parent = QVBoxLayout()
        layout_control =QHBoxLayout()
        layout_plots = QVBoxLayout()

        # plot area
        layout_plots.addWidget(self.canvas)

        # controls
        layout_control.addWidget(self.dropdown)
        layout_control.addWidget(self.event_dropdown)

        layout_parent.addLayout(layout_control)
        layout_parent.addLayout(layout_plots)

        return layout_parent

    def populate_events(self, events: list[tuple[int, str]]):
        self.event_dropdown.blockSignals(True)
        self.event_dropdown.clear()
        self.event_dropdown.addItem("Select an event...", userData=None)
        for idx, name in events:
            self.event_dropdown.addItem(name, userData=idx)
        self.event_dropdown.blockSignals(False)

    def populate_dropdown(self, signals: list[tuple[int, str]]):
        self.dropdown.blockSignals(True)
        self.dropdown.clear()
        self.dropdown.addItem("Select a Signal...", userData=None)
        for x, name in signals:
            self.dropdown.addItem(name, userData=x)
        self.dropdown.blockSignals(False)

    def _on_selection_change(self, index: int):
        selected_id = self.dropdown.itemData(index)
        if selected_id is not None:
            self.signal_selected.emit(selected_id)

    def _on_event_change(self, index: int):
        selected_event_id = self.event_dropdown.itemData(index)
        selected_id = self.dropdown.itemData(self.dropdown.currentIndex())
        if selected_id is not None:
            self.event_selected.emit(selected_id, selected_event_id)

    #### plotting functions
    def _draw_plots(self):
        self.canvas.draw()

    def update_plots(self, x_vector: np.ndarray, x_vector_short: np.ndarray,
                     t_vector: np.ndarray, t_vector_short: np.ndarray,
                     phase_vector: np.ndarray,
                     freqs: np.ndarray, F: np.ndarray,
                     Spec:np.ndarray, extent: tuple[float, float, float, float],
                     xcorr: np.ndarray = None,
                     event_start:int = None,
                     event_end: int= None):
        for name, ax in self.axes.items():
            ax.clear()
        self._update_ts(t_vector, x_vector, event_start=event_start, event_end=event_end)
        self._update_fft(freqs, F)
        self._update_phase(t_vector_short, phase_vector)
        self._update_spectrogram(z=Spec, ex=extent)
        self._update_const(x_vector_short)
        if xcorr is not None:
            self._update_xcorr(t_vector, xcorr, event_start=event_start, event_end=event_end)
        self._draw_plots()

    def _update_ts(self, x: np.ndarray, y: np.ndarray, event_start:int = None, event_end:int =None):
        ax = self.axes["timeseries"]
        ax = plot_iq_timeseries(ax=ax, t=x, iq=y)
        if event_start is not None:
            ax = plot_event_window(ax=ax, t=x, start_idx=event_start, end_idx=event_end)


    def _update_xcorr(self, x: np.ndarray, y: np.ndarray, event_start:int = None, event_end:int =None):
        ax = self.axes["xcorr"]
        ax = plot_iq_timeseries(ax=ax, t=x, iq=y)
        if event_start is not None:
            ax = plot_event_window(t=x, ax=ax, start_idx=event_start, end_idx=event_end)

    def _update_fft(self, x: np.ndarray, y: np.ndarray):
        ax = self.axes["fft"]
        ax = plot_fft(f=x, F=y, ax=ax)


    def _update_phase(self, x: np.ndarray, y: np.ndarray):
        ax = self.axes["phase"]
        ax = plot_phase(t=x, P=y, ax=ax)


    def _update_spectrogram(self, ex: tuple[float, float, float, float], z: np.ndarray):
        self._clear_colorbar()
        ax = self.axes["spectrogram"]
        ax = plot_spectrogram(S=z, extent=ex, ax=ax, colorbar=False)
        m = z[np.isfinite(z)].max()
        print(m)
        print(type(m))
        norm = Normalize(vmin=m-90, vmax=m)
        sm = ScalarMappable(norm=norm, cmap="jet")
        self.spectrogram_cbar = self.figure.colorbar(sm, ax=ax)


    def _update_const(self, x: np.ndarray):
        ax = self.axes["const"]
        ax = plot_complex_distribution(x=x, ax=ax)

    def _clear_colorbar(self):
        if self.spectrogram_cbar is not None:
            self.spectrogram_cbar.remove()
            self.spectrogram_cbar = None



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