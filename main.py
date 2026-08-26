from dataclasses import dataclass
from typing import List

from core.antennas.array import AntennaArray
from core.dsp.analog_to_digital import adc
from core.dsp.signal_new import Signal

from views.windows.run_window_as_app import create_app
from views.windows.init_view.init_view import init_view
from views.windows.SignalAnalyzer.Overview import overview
from views.windows.MainView import MainView

from controllers.MainController import MainController
from controllers.init_controller import InitController
from controllers.ada_controller import AdaController
from controllers.overview_controller import SignalOverviewController
from controllers.AppState import AppState
import sys


def main():
    app = create_app()
    state = AppState()

    ini_v = init_view()
    ovr_v = overview()
    main_v = MainView(init_view=ini_v, overview_view=ovr_v)

    main_ctrl = MainController(view=main_v, state=state)

    main_v.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
