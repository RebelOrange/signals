from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget

class MainView(QMainWindow):
    def __init__(self, init_view: QWidget, overview_view: QWidget):
        super().__init__()
        self.setWindowTitle("Signal Processing Workbench")
        self.resize(1200, 800)

        # Retain references to child view widgets
        self.init_view = init_view
        self.overview_view = overview_view

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(self.init_view, "Simulation Setup")
        self.tabs.addTab(self.overview_view, "Signal Overview")

    def set_tab_enabled(self, index: int, enabled: bool) -> None:
        self.tabs.setTabEnabled(index, enabled)

    def set_active_tab(self, index: int) -> None:
        self.tabs.setCurrentIndex(index)