#from controllers.base_controller import BaseController
from views.windows.init_view.init_view import init_view
from views.windows.init_view.ConfigDialog import DynamicConfigDialog
from core.antennas.array import ElementPatterns, AntennaArray
from core.antennas.classic.ULA import ULA

class InitController:
    def __init__(self, view: init_view, antenna: AntennaArray, DynamicConfigDialog = None):
        self.view = view
        self.antenna = antenna
        self._connect_signals()

    def _connect_signals(self) -> None:
        self.view.preview_requested.connect(self._handle_preview)
        self.view.simulation_requested.connect(self._handle_sim)

    def _handle_preview(self, params: dict) -> None:
        print(f"plotting preview scenario:")
        for k, v in params.items():
            print(f"\t{k}: {v}")

        ssl_taylor = 25
        num_antenna_elements = params["num_antenna_elements"]
        main_order = params["main_order"]
        # make antenna for spatial response plot
        self.antenna = ULA(num_elements=num_antenna_elements)
        patterns = ([ElementPatterns.taylor_subarray(num_sub_elements=main_order, sll_db=ssl_taylor)]
                    + [ElementPatterns.delta_subarray(4, gain_offset=(-ssl_taylor + 3))] * (num_antenna_elements - 1))
        self.antenna.set_disconnected_elements(params["disconnected_elements"])
        self.antenna.set_patterns(patterns)

        doas = params["doas"]
        pattern_resp_names = ["main", "aux_0", "aux_1", "aux_2", "aux_3", "aux_4", "aux_5", "aux_6", "aux_7", "aux_8",
                              "aux_9"]
        az_points, pattern_resp = self.antenna.element_pattern_response()
        self.view._update_antenna_preview(pattern_responses=pattern_resp, az_points=az_points,
                                    pattern_labels=pattern_resp_names, doas=doas)
        self.view._draw_plots()
        pass

    def _handle_sim(self) -> None:
        print("handled sim")
        pass
