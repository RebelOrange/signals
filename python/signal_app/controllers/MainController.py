from views.windows.MainView import MainView
from controllers.init_controller import InitController
from controllers.overview_controller import SignalOverviewController
from controllers.AdaController import AdaController
from controllers.VitisController import VitisController
from .AppState import AppState
from core.dsp.data_loader.DataLoader import export_to_csv
from core.vitis.PyVitis import run_vitis_csim


class MainController:
    def __init__(self, view: MainView, state: AppState):
        self.view = view
        self.state = state

        # Instantiating child controllers with their corresponding views
        self.init_ctrl = InitController(view=self.view.init_view, state=self.state)
        self.ovr_ctrl = SignalOverviewController(view=self.view.overview_view, state=self.state)
        self.ada_ctrl = AdaController(view=self.view.ada_view, state=self.state)
        self.vitis_ctrl = VitisController(view=self.view.vitis_view, state=self.state)

        # Disable downstream tabs initially
        self.view.set_tab_enabled(1, False)
        self.view.set_tab_enabled(2, False)
        self.view.set_tab_enabled(3, False)

        self._connect_signals()

    def _connect_signals(self) -> None:
        # Listen for simulation completion from InitController
        self.init_ctrl.signals.run_event.connect(self._on_simulation_finished)

    def _on_simulation_finished(self, d: int) -> None:
        print("Simulation complete. MainController unlocking tabs.")
        # export sim data for vitis/vivado
        export_to_csv(self.state.adc_inst.X_dig, filename=self.state.iq_data_path+"input_iq.csv")

        self.view.show_wait_window()
        # TODO: needs to wait for vitis to finish subprocess
        TB_EXE = "/opt/rfdev-envs/hls/ada_filt/multi_lms/build/"
        M_PARAM = 0.1
        run_vitis_csim(TB_EXE, "run_csim.tcl", M_PARAM)
        self.vitis_ctrl._load_vitis_data()
        self.view.close_wait_window()

        # run simulation model
        # 1. Enable Overview Tab
        self.view.set_tab_enabled(1, True)
        self.view.set_tab_enabled(2, True)
        self.view.set_tab_enabled(3, True)

        # 2. Tell downstream controller to refresh its view using the new AppState
        self.ovr_ctrl.update_view_from_state()
        self.ada_ctrl.update_view_from_state()
        self.vitis_ctrl.update_view_from_state()

        # 3. Focus the Overview tab
        self.view.set_active_tab(1)