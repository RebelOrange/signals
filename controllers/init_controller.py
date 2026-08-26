#from controllers.base_controller import BaseController
from views.windows.init_view.init_view import init_view
from views.windows.init_view.ConfigDialog import DynamicConfigDialog
from core.antennas.array import ElementPatterns, AntennaArray
from core.antennas.classic.ULA import ULA
from .simulation_model import sim_case_0
from typing import List
from PyQt5.QtCore import QObject, pyqtSignal
from .AppState import AppState

# 1. Tiny helper class strictly for the signal infrastructure
class ControllerSignals(QObject):
    run_event = pyqtSignal(int)

from core.dsp.signal_new import Signal


class InitController:
    def __init__(self, view: init_view, state: AppState):
        self.signals = ControllerSignals()
        self.view = view
        self.state = state
        self._connect_signals()

    def _connect_signals(self) -> None:
        self.view.preview_requested.connect(self._handle_preview)
        self.view.simulation_requested.connect(self._handle_sim)

    def _handle_preview(self, params: dict) -> None:
        print(f"plotting preview scenario:")
        for k, v in params.items():
            print(f"\t{k}: {v}")

        ssl_taylor = params["sll"]
        print(f"sidelobe level: {ssl_taylor}")
        num_antenna_elements = params["num_antenna_elements"]
        main_order = params["main_order"]
        # make antenna for spatial response plot
        self.state.antenna = ULA(num_elements=num_antenna_elements)
        patterns = ([ElementPatterns.taylor_subarray(num_sub_elements=main_order, sll_db=ssl_taylor)]
                    + [ElementPatterns.delta_subarray(4, gain_offset=(-ssl_taylor + 3))] * (num_antenna_elements - 1))
        self.state.antenna.set_disconnected_elements(params["disconnected_elements"])
        self.state.antenna.set_patterns(patterns)

        doas = params["doas"]
        pattern_resp_names = ["main", "aux_0", "aux_1", "aux_2", "aux_3", "aux_4", "aux_5", "aux_6", "aux_7", "aux_8",
                              "aux_9"]
        az_points, pattern_resp = self.state.antenna.element_pattern_response()
        self.view._update_antenna_preview(pattern_responses=pattern_resp, az_points=az_points,
                                    pattern_labels=pattern_resp_names, doas=doas)
        self.view._draw_plots()
        pass

    def _handle_sim(self, p: dict) -> None:
        print("handled sim")
        for k, v in p.items():
            print(f"\t{k}: {v}")

        tgt_config = p["tgt_config"]

        self.state.input_sigs, self.state.rx_sigs, self.state.antenna, self.state.adc_inst, self.state.adc_sigs = sim_case_0(tgt_config=tgt_config,
                                                                    tgt_on=p["tgt_on"],
                                                                    num_jammers=p["num_jammers"],
                                                                    tgt_SNR=3,
                                                                    jam_SNRs=p["jam_SNRs"],
                                                                    jam_doas=p["doas"],
                                                                    sidelobe_gain_offset=p["sidelobe_gain_offset"],
                                                                    bw_range_jammer=p["bw_range_jammer"],
                                                                    min_gate_range_jammer=p["min_gate_range_jammer"],
                                                                    max_gate_range_jammer=p["max_gate_range_jammer"],
                                                                    disconnected_elements=p["disconnected_elements"])
        print("created simulation data")
        self.signals.run_event.emit(0)
        pass
