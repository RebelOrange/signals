import pandas as pd
import numpy as np

from views.windows.AdaptiveFilter.ada_overview import ada_overview
from .AppState import AppState
from core.dsp.signal_new import Signal
from core.dsp.signal_analyzer.signal_analyzer import SignalAnalyzer
from core.dsp.algorithms.canceller_algorithms.providers.Wiener import Wiener
from typing import Optional

class VitisController:
    def __init__(self, view: ada_overview, state: AppState):
        self.view = view
        self.state = state
        self.names: list[tuple[int, str]] = []
        self.sig_dict: dict[int, tuple[str, Signal]] = {}
        self._connect_signals()
        self.iq_folder = state.iq_data_path
        self.weights_folder = state.iq_data_path


    def _connect_signals(self):
        self.view.control_changed.connect(self._handle_control_event)
        pass

    def _load_vitis_data(self):
        iq_df = pd.read_csv(self.iq_folder+"/vitis/csim_iq_output.csv")
        print(iq_df.head())
        print(iq_df.keys())
        I = iq_df['csim_r'].values
        Q = iq_df['csim_i'].values
        self.vitis_iq: np.ndarray = I + 1j*Q

        order = self.state.antenna.num_elements-1

        #weight_df = pd.read_csv(self.weights_folder+"/vitis/vitis_sim_output.csv")
        self.vitis_W = np.zeros((order, len(self.vitis_iq)), dtype=np.complex128)
        """for i in range(order):
            w_I = weight_df[f"w{i}_r"]
            w_Q = weight_df[f"w{i}_t"]
            self.vitis_W[i, :] = w_I + 1j*w_Q
        """
        self.vitis_iq.transpose()

        #TODO: maybe convert state vitis references to a list so multiple algorithms can be viewed
        self.state.vitis_iq = self.vitis_iq
        self.state.vitis_weights = self.vitis_W

    def _get_state(self):
        self.event_names = []
        for idx, e in enumerate(self.state.rx_sigs[0].events):
            self.event_names.append((idx, e.label))

        self.d = self.state.adc_inst.X_dig[0,:]
        self.X = self.state.adc_inst.X_dig[1:,:]
        self.mf = self.state.input_sigs[0].events[0].pulse_iq
        self.eig_val, self.eig_vec = SignalAnalyzer.eigenvalue_decomp(self.X)
        self.M_aux = self.X.shape[0]
        self.K_taps = 1 # FIR order
        self.ktb_var = 10**(self.state.adc_inst.ktb_db_int16/10)

        wien = Wiener(X=self.X, d=self.d, order=self.K_taps)
        self.wien_iq, _, self.wien_W = wien.run()
        self.t = self.state.input_sigs[0].t

    def _handle_control_event(self, event_id: Optional[int] = None,
                              mf_bool: Optional[bool] = False,
                              power_bool: Optional[bool] = False,):
        # handle event extraction
        wien = Wiener(X=self.X, d=self.d, order=self.K_taps)
        wien_iq, _, wien_W = wien.run()
        plot_main = self.d
        plot_opt = wien_iq
        plot_alg = self.vitis_iq
        plot_W = self.vitis_W
        t = self.t
        ktb_var = self.ktb_var

        if event_id is None:
            event_id = 0
        elif event_id == -1:
            event_id = 0
        else:
            print(f"Controller recieved event index {event_id}")

        event = self.state.rx_sigs[0].events[event_id]
        event_start = event.start_idx
        event_end = event.end_idx

        if mf_bool:
            plot_main = np.abs(SignalAnalyzer.matched_filter(self.d, self.mf))
            plot_opt = np.abs(SignalAnalyzer.matched_filter(wien_iq, self.mf))
            plot_alg = np.abs(SignalAnalyzer.matched_filter(self.vitis_iq, self.mf))

        if power_bool:
            ktb_var = 10*np.log10(np.abs(ktb_var+1e-1))
            plot_main = 20*np.log10(np.abs(plot_main+1e-1))
            plot_opt = 20*np.log10(np.abs(plot_opt+1e-1))
            plot_alg = 20*np.log10(np.abs(plot_alg+1e-1))

            event_start = None
            event_end = None

        if event_start is not None:
            wien_event = Wiener(X=self.X[:, event_start:event_end], d=self.d[event_start:event_end], order=self.K_taps)
            _, _, wien_W = wien_event.run()
            eig_val, eig_vec = SignalAnalyzer.eigenvalue_decomp(self.X[:,event_start:event_end])
        else:
            eig_val, eig_vec = SignalAnalyzer.eigenvalue_decomp(self.X)

        self.view.update_plots(main_iq=plot_main,opt_iq=plot_opt,alg_iq=plot_alg,
                               t=t,
                               noise_floor=ktb_var,
                               opt_weights=wien_W, alg_weights=plot_W,
                               eig_val=eig_val,eig_vec=eig_vec,
                               event_start=event_start,event_end=event_end)

    def update_view_from_state(self):
        self._get_state()
        self.view.update_plots(main_iq=self.d,opt_iq=self.wien_iq,alg_iq=self.vitis_iq,
                               t = self.t,
                               eig_val = self.eig_val, eig_vec = self.eig_vec,
                               opt_weights=self.wien_W, alg_weights=self.vitis_W)
        self.view.populate_events(self.event_names)




