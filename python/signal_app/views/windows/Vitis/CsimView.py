from PyQt5.QtWidgets import QWidget, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from mpl.dsp.signal_plotter import *
from mpl.axis_config import *

class CsimView(QWidget):
    def __init__(self):
        super().__init__()
        self.figure: Figure = Figure(constrained_layout=True)
        self.axes: Axes
        self.canvas: FigureCanvas

        self.setLayout(self._layout())

    def _layout(self):
        l = QHBoxLayout()

        return l

    def _init_figures(self):
        pass