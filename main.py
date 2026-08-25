from dataclasses import dataclass
from typing import List

from core.antennas.array import AntennaArray
from core.dsp.analog_to_digital import adc
from core.dsp.signal_new import Signal
from views.windows.run_window_as_app import create_app
from views.windows.init_view.init_view import init_view
from controllers.init_controller import InitController
import sys

@dataclass
class AppState:
    antenna: AntennaArray = None
    input_sigs: List[Signal] = None
    rx_sigs: List[Signal] =None
    adc_inst: adc = None
    adc_sigs: List[Signal] = None



def main():
    app = create_app()

    # view initialization
    ini_view = init_view()

    # model
    state = AppState()

    # controller initialization
    ini_ctrl = InitController(view=ini_view, antenna=state.antenna)

    ini_view.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
