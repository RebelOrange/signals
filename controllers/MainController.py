from views.windows.MainView import MainView
from controllers.init_controller import InitController
from controllers.overview_controller import SignalOverviewController
from .AppState import AppState


class MainController:
    def __init__(self, view: MainView, state: AppState):
        self.view = view
        self.state = state

        # Instantiating child controllers with their corresponding views
        self.init_ctrl = InitController(view=self.view.init_view, state=self.state)
        self.ovr_ctrl = SignalOverviewController(view=self.view.overview_view, state=self.state)

        # Disable downstream tabs initially
        self.view.set_tab_enabled(1, False)

        self._connect_signals()

    def _connect_signals(self) -> None:
        # Listen for simulation completion from InitController
        self.init_ctrl.signals.run_event.connect(self._on_simulation_finished)

    def _on_simulation_finished(self, d: int) -> None:
        print("Simulation complete. MainController unlocking tabs.")

        # run simulation model
        

        # 1. Enable Overview Tab
        self.view.set_tab_enabled(1, True)

        # 2. Tell downstream controller to refresh its view using the new AppState
        self.ovr_ctrl.update_view_from_state()

        # 3. Focus the Overview tab
        self.view.set_active_tab(1)