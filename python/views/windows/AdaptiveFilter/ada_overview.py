from PyQt5.QtCore import pyqtSignal
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import Normalize

from views.windows.run_window_as_app import *
from PyQt5.QtWidgets import QWidget, QComboBox, QHBoxLayout, QVBoxLayout, QCheckBox

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.colorbar
from matplotlib.cm import ScalarMappable

from mpl.dsp.signal_plotter import *
from mpl.axis_config import *
from itertools import chain
from dataclasses import dataclass

"""
@dataclass
class ada_ovr_ctrl_states:
    event_dropdown: QComboBox = QComboBox()
    match_filter_checkbox: QCheckBox = QCheckBox()
    power_plot_checkbox: QCheckBox = QCheckBox()

    def __post_init__(self):
        self.event_dropdown.addItem("Select a signal...", userData=None)
        self.match_filter_checkbox.setCheckable(False)
        self.power_plot_checkbox.setCheckable(False)
    """


class ada_overview(QWidget):

    # signals
    control_changed = pyqtSignal(int, bool, bool)

    ##################### initialization and layout setup #################
    def __init__(self):
        super().__init__()

        # control elements
        #self.ctrl = ada_ovr_ctrl_states()
        self.event_dropdown: QComboBox = QComboBox()
        self.match_filter_checkbox: QCheckBox = QCheckBox("Enable Matched Filter")
        self.power_plot_checkbox: QCheckBox = QCheckBox("Plot dB Scale")


        # figures
        self.iq_figure: Figure = Figure(constrained_layout=True)
        self.iq_axes: Axes
        self.iq_canvas: FigureCanvas
        self.w_figure: Figure = Figure(constrained_layout=True)
        self.w_axes: Axes
        self.w_canvas: FigureCanvas

        self.setLayout(self._layout())

    def _init_ui(self):
        self._init_ctrl()
        self._init_iq_figure()
        self._init_weight_figure()

    def _init_ctrl(self):
        # connect control elements to signals
        self.event_dropdown.currentIndexChanged.connect(self._on_signal_change)
        self.power_plot_checkbox.stateChanged.connect(self._on_ctrl_change)
        self.match_filter_checkbox.stateChanged.connect(self._on_ctrl_change)

    def _init_iq_figure(self):
        mosaic_layout = [["main_channel"],
                         ["opt_filt"],
                         ["alg_filt"]]
        self.iq_axes = self.iq_figure.subplot_mosaic(mosaic_layout)
        for name, ax in self.iq_axes.items():
            ax.set_title(name)
        self.iq_canvas = FigureCanvas(self.iq_figure)

    def _init_weight_figure(self):
        mosaic_layout = [["weight_plane", "R_xx"],
                         ["final_weights", "convergence"]]
        self.w_axes = self.w_figure.subplot_mosaic(mosaic_layout)
        for name, ax in self.w_axes.items():
            ax.set_title(name)
        self.w_canvas = FigureCanvas(self.w_figure)

    def _layout(self):
        self._init_ui()

        layout_parent = QHBoxLayout()

        layout_left = QVBoxLayout()
        layout_ctrl = QVBoxLayout()
        layout_iq = QVBoxLayout()

        layout_right = QVBoxLayout()

        # add widgets
        layout_ctrl.addWidget(self.event_dropdown)
        layout_ctrl.addWidget(self.match_filter_checkbox)
        layout_ctrl.addWidget(self.power_plot_checkbox)

        layout_iq.addWidget(self.iq_canvas)
        layout_right.addWidget(self.w_canvas)

        # assign layouts
        layout_left.addLayout(layout_ctrl)
        layout_left.addLayout(layout_iq)

        layout_parent.addLayout(layout_left)
        layout_parent.addLayout(layout_right)

        return layout_parent

    ########################## control event handling ###################
    def _on_signal_change(self, idx:int):
        selected_event_id = self.event_dropdown.itemData(idx)
        mf = self.match_filter_checkbox.isChecked()
        power = self.power_plot_checkbox.isChecked()
        self.control_changed.emit(selected_event_id, mf, power)

    def _on_ctrl_change(self):
        idx = self.event_dropdown.currentIndex()
        selected_event_id = self.event_dropdown.itemData(idx)
        mf = self.match_filter_checkbox.isChecked()
        power = self.power_plot_checkbox.isChecked()
        self.control_changed.emit(selected_event_id, mf, power)

    ######################## Data loading and plotting ##################
    #mosaic_layout = [["weight_plane", "R_xx"],
    #                 ["final_weights", "convergence"]]
    def _update_scree_plot(self, eigs):
        ax = self.w_axes["R_xx"]
        x = np.arange(len(eigs))
        ax.stem(10*np.log10(eigs))
        ax.set_title("R_xx Eigenvalues")
        ax.grid(True)
        ax.set_ylabel("Power (dB)")
        ax.set_xlabel("Index")

    def _update_final_weights(self, w_opt, w_alg,
                                    event_start: int = None,
                                    event_end:int = None):
        ax = self.w_axes["final_weights"]
        ax.set_title("Final Weights")
        M, L = np.shape(w_alg) # M channels, L samples
        if event_start is None:
            event_start=0
            event_end=L
        x = np.ones((1,event_end-event_start))
        for m in range(M):
            ax.plot(m, np.abs(w_opt[m]), "o",label="Optimal", mfc="b")
            ax.plot(np.squeeze(x*m), np.abs(w_alg[m,event_start:event_end]), ".",label="Algorithm", mfc="r", alpha=0.1)
        ax.grid(True)
        ax.set_ylabel("Amplitude")
        ax.set_xlabel("Aux Antenna Element")
        ax.legend(loc="upper right")


    def _update_weight_constelation(self, w_opt, w_alg,
                                    event_start: int = None,
                                    event_end:int = None):
        if w_opt is None:
            return
        M, L = np.shape(w_alg) # M channels, L samples
        if event_start is None:
            event_start=0
            event_end=L
        ax = self.w_axes["weight_plane"]
        for m in range(M):
            w = np.squeeze(w_alg[m,event_start:event_end])
            l, = ax.plot(w.real, w.imag, ".", label=f"W_alg {m}", alpha=0.2)
            color = l.get_color()
            w = np.squeeze(w_opt[m])
            ax.plot(w.real, w.imag, "^", mec="k", mfc=color, label=f"W_opt {m}")

        lims = 1.25*np.max(np.abs(w_opt))
        ax.set_ylim([-lims, lims])
        ax.set_xlim([-lims, lims])
        ax.set_title("Complex Weights")
        ax.grid(True)
        ax.set_ylabel("Imaginary")
        ax.set_xlabel("Real")
        ax.legend(loc="upper right")


    def _update_ts(self, main_iq: np.ndarray, opt_iq:np.ndarray, alg_iq:np.ndarray,
                   t: np.ndarray,
                   noise_floor: float = None,
                   event_start:int = None, event_end:int = None):
        ax = self.iq_axes["main_channel"]
        ax = plot_iq_timeseries(ax=ax, t=t, iq=main_iq)
        if event_start is not None:
            ax = plot_event_window(ax=ax, t=t, start_idx=event_start, end_idx=event_end)
        # scale ylims to max of main channel
        ylim = (np.min(main_iq.real), np.max(main_iq.real))
        ax.set_ylim(ylim)

        ax = self.iq_axes["opt_filt"]
        ax = plot_iq_timeseries(ax=ax, t=t, iq=opt_iq)
        if event_start is not None:
            ax = plot_event_window(ax=ax, t=t, start_idx=event_start, end_idx=event_end)
        ax.set_ylim(ylim)

        ax = self.iq_axes["alg_filt"]
        ax = plot_iq_timeseries(ax=ax, t=t, iq=alg_iq)
        if event_start is not None:
            ax = plot_event_window(ax=ax, t=t, start_idx=event_start, end_idx=event_end)
        ax.set_ylim(ylim)

        if noise_floor is not None:
            for name, ax in self.iq_axes.items():
                ax.plot([t[0], t[-1]], [noise_floor, noise_floor], "r--", label="kTB")
                ax.legend()

    def populate_events(self, events: list[tuple[int, str]]):
        self.event_dropdown.blockSignals(True)
        self.event_dropdown.clear()
        self.event_dropdown.addItem("Select a signal...", userData=-1)
        for idx, name in events:
            self.event_dropdown.addItem(name, userData=idx)
        self.event_dropdown.blockSignals(False)

    def update_plots(self, main_iq: np.ndarray, opt_iq:np.ndarray, alg_iq:np.ndarray,
                     t: np.ndarray,
                     noise_floor: float = None,
                     opt_weights: np.ndarray = None, alg_weights: np.ndarray = None,
                     eig_val:np.ndarray= None, eig_vec:np.ndarray =None,
                     event_start:int = None, event_end:int = None):
        for (name, ax) in chain(self.iq_axes.items(), self.w_axes.items()):
            ax.clear()
        self._update_ts(main_iq=main_iq, opt_iq=opt_iq, alg_iq=alg_iq,
                        t=t,
                        noise_floor=noise_floor,
                        event_start=event_start, event_end=event_end)
        self._update_weight_constelation(w_opt=opt_weights, w_alg=alg_weights,
                                    event_start=event_start, event_end=event_end)
        if eig_val is not None:
            self._update_scree_plot(eig_val)
        self._update_final_weights(w_opt=opt_weights, w_alg=alg_weights,
                                   event_start=event_start, event_end=event_end)

        self._draw_plots()

    def _draw_plots(self):
        self.iq_canvas.draw_idle()
        self.w_canvas.draw_idle()

if __name__ == "__main__":

    from tests.test_cases.adc_test import multiple_jammer_case_with_adc, calculate_leaky_gamma
    from itertools import chain
    from core.dsp.signal_new import Signal
    from core.dsp.signal_analyzer.signal_analyzer import SignalAnalyzer
    from core.dsp.algorithms.canceller_algorithms.providers.LMS import nlms
    from core.dsp.algorithms.canceller_algorithms.providers.Wiener import Wiener
    from typing import Optional

    jam_SNRs = [20, 22, 24, 20, 20, 20]
    jam_SNRs = None
    jam_SNRs = [30, 10, 5, 0, 3, 8, 1]
    #jam_SNRs = [40, 0, 5, 0, 3, 8, 1]
    disconnected_elements = [8]
    input_sigs, mixed_sigs, antenna, adc = multiple_jammer_case_with_adc(tgt_on=True,
                                                                    num_jammers=5,
                                                                    num_antenna_elements=8,
                                                                    jam_SNRs=jam_SNRs,
                                                                    jam_bw_range = [0.5, 0.5],
                                                                    doas=[15.0, -26.0, 33.0, -33.0, 25.0, 10.0, -15.0],
                                                                    min_gate_range_jammer=[0.2,0.2],
                                                                    max_gate_range_jammer=[0.8,0.8],
                                                                     disconnected_elements=disconnected_elements)

    A_n = antenna.A_n
    print(f"Noisy Matrix Condition number: {np.linalg.cond(A_n):0.2f}")
    #input_sigs, mixed_sigs, antenna = multiple_jammer_case_0(tgt_on=True,
    #                                                         num_jammers=3,
    #                                                         num_antenna_elements=8,
    #                                                         jam_SNRs=jam_SNRs)
    sig = mixed_sigs[0] # signal for time vector and events
    event_names = []
    for idx, e in enumerate(mixed_sigs[0].events):
        event_names.append((idx, e.label))

    mf = input_sigs[0].events[0].pulse_iq
    gamma = calculate_leaky_gamma(noise_bits=4, jnr_min_db=0, margin_db=0)
    #gamma = 0
    print(f"Using leaky lms gamma {gamma}")
    mu = 0.05
    ################### controller preprocessing steps? #################
    # extract canceller algorithm channels, and do some stats
    X = adc.X_dig[1:,:]
    d = adc.X_dig[0,:]

    R_xx = X@X.conj().T
    eig_val, eig_vec = SignalAnalyzer.eigenvalue_decomp(X)
    print(f"R_xx Rank: {np.linalg.matrix_rank(R_xx)}")
    print(f"R_xx condition number: {np.linalg.cond(R_xx):0.2f}")
    print(f"R_xx Eigen Values:")
    for val in eig_val.real:
        print(f"   {val}")
    spread = np.max(eig_val.real)/np.min(eig_val.real)
    print(f"Eigenvalue spread: {spread:0.2f} ({10*np.log10(spread)})")



    # Extract dynamic power parameters from antenna and generated signals
    M_aux = X.shape[0]  # 7 auxiliary channels
    K_taps = 1 # FIR order
    ktb_var = 10**(adc.ktb_db_int16/10)  # Thermal noise floor

    # Estimate actual jammer power bounds from signal matrices
    X_aux = X
    ch_powers = np.mean(np.abs(X_aux) ** 2, axis=1)
    var_jam_min = np.min(ch_powers)
    var_jam_max = np.max(ch_powers)

    #print(f"Calculated Leaky LMS gamma: {gamma:.4e}")

    # LMS object, Wiener Object
    lms = nlms(X=X, d=d, mu=mu, order=K_taps, gamma=gamma)
    wien = Wiener(X=X, d=d, order=K_taps)
    lms_iq, _, lms_W = lms.run()
    wien_iq, _, wien_W = wien.run()
    t = input_sigs[0].t

    ################ controller event handling (assumes alg data precomputed) ######
    def handle_ctrl_event(event_id: Optional[int] = None,
                          mf_bool: Optional[bool] = False,
                          power_bool: Optional[bool] = False):
        # handle event extraction
        event_start = None
        event_end = None
        lms = nlms(X=X, d=d, mu=mu, order=K_taps, gamma=gamma)
        wien = Wiener(X=X, d=d, order=K_taps)
        lms_iq, _, lms_W = lms.run()
        wien_iq, _, wien_W = wien.run()
        plot_main = d
        plot_opt = wien_iq
        plot_alg = lms_iq
        t = sig.t
        ktb_var = 10**(adc.ktb_db_int16/10)
        if event_id is None:
            event_id = 0
        elif event_id == -1:
            event_id = 0
        else:
            print(f"Controller recieved event index {event_id}")
        event = sig.events[event_id]
        event_start = event.start_idx
        event_end = event.end_idx

        # handle matched filter checkbox befor power plot
        if mf_bool:
            # need to adjust ktb noise somehow?? maybe generate white noise with
            # ktb variance and run matched filter?
            plot_main = np.abs(SignalAnalyzer.matched_filter(d, mf))
            plot_opt = np.abs(SignalAnalyzer.matched_filter(wien_iq, mf))
            plot_alg = np.abs(SignalAnalyzer.matched_filter(lms_iq, mf))

        # handle power plot checkbox
        if power_bool:
            ktb_var = 10*np.log10(np.abs(ktb_var+1e-1))
            plot_main = 20 * np.log10(np.abs(plot_main+1e-1))
            plot_opt = 20 * np.log10(np.abs(plot_opt+1e-1))
            plot_alg = 20 * np.log10(np.abs(plot_alg+1e-1))

            # need to fix scalling on power plot
            event_start = None
            event_end = None

        if event_start is not None:
            wien_event = Wiener(X=X[:,event_start:event_end], d=d[event_start:event_end], order=K_taps)
            _, _, wien_W = wien_event.run()
            eig_val, eig_vec = SignalAnalyzer.eigenvalue_decomp(X[:,event_start:event_end])
        else:
            eig_val, eig_vec = SignalAnalyzer.eigenvalue_decomp(X)

        ovr.update_plots(main_iq=plot_main, opt_iq=plot_opt, alg_iq=plot_alg,
                         t=t,
                         noise_floor=ktb_var,
                         opt_weights=wien_W, alg_weights=lms_W,
                         eig_val=eig_val, eig_vec=eig_vec,
                         event_start=event_start, event_end=event_end)



    ################ view init ##################
    app = create_app()
    ovr = ada_overview()
    # signal connects

    # initial data load
    eig_val, eig_vec = SignalAnalyzer.eigenvalue_decomp(X)
    ovr.update_plots(main_iq=d, opt_iq=wien_iq, alg_iq=lms_iq,
                     t=t,
                     eig_val=eig_val,
                     opt_weights=wien_W, alg_weights=lms_W)
    ovr.populate_events(event_names)
    ovr.control_changed.connect(handle_ctrl_event)
    run_window_as_app(win=ovr)

