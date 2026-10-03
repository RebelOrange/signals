from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QProgressDialog


class MainView(QMainWindow):
    def __init__(self, init_view: QWidget, overview_view: QWidget, ada_view: QWidget, vitis_view: QWidget):
        super().__init__()
        self.setWindowTitle("Signal Processing Workbench")
        self.resize(1200, 800)

        # Retain references to child view widgets
        self.init_view = init_view
        self.overview_view = overview_view
        self.ada_view = ada_view
        self.vitis_view = vitis_view

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(self.init_view, "Simulation Setup")
        self.tabs.addTab(self.overview_view, "Signal Overview")
        self.tabs.addTab(self.ada_view, "Algorithm View")
        self.tabs.addTab(self.vitis_view, "Vitis CSIM View")

        #wait dialog box for long wait times
        self.wait_diag = QProgressDialog("Running Vitis/Vivado, please wait...", None, 0,0, self)
        self.wait_diag.setWindowTitle("Unknown")
        self.wait_diag.setCancelButton(None)
        self.wait_diag.setModal(True)

    def show_wait_window(self):
        self.wait_diag.show()

    def close_wait_window(self):
        self.wait_diag.close()
        print("Vitis/Vivado finished.")

    def set_tab_enabled(self, index: int, enabled: bool) -> None:
        self.tabs.setTabEnabled(index, enabled)

    def set_active_tab(self, index: int) -> None:
        self.tabs.setCurrentIndex(index)