from PyQt5.QtWidgets import QWidget
from views.windows.run_window_as_app import *

class SignalAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.name = "Signal Analyzer"


if __name__ == "__main__":
    app = create_app()
    sig_an = SignalAnalyzer()
    run_window_as_app(win=sig_an)