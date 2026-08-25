#from controllers.base_controller import BaseController
from views.windows.AdaptiveFilter.ada_overview import ada_overview
from views.windows.init_view.ConfigDialog import DynamicConfigDialog
from core.antennas.array import ElementPatterns, AntennaArray
from core.antennas.classic.ULA import ULA

class AdaController:
    def __init__(self, view: ada_overview, antenna: AntennaArray, DynamicConfigDialog = None):
        self.view = view
        self.antenna = antenna
        self._connect_signals()

    def _connect_signals(self):
        pass