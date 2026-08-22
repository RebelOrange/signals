from PyQt5.QtCore import pyqtSignal
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.colors import Normalize

from views.windows.run_window_as_app import *
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
    QGroupBox, QCheckBox, QSpinBox, QLineEdit, QPushButton,
    QMessageBox, QComboBox
)
import re
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.colorbar
from matplotlib.cm import ScalarMappable

from mpl.dsp.signal_plotter import *
from mpl.axis_config import *

from dataclasses import dataclass

class init_view(QWidget):
    simulation_requested = pyqtSignal(dict)
    preview_requested = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulation Parameter Setup")
        self.resize(500, 600)
        self.figure: Figure = Figure(constrained_layout=True)
        self.axes: Axes
        self.canvas: FigureCanvas
        self._init_ui()

    def _init_ui(self):
        self.setLayout(self._layout())

    def _layout(self):
        main_layout = QHBoxLayout()
        layout_entry = QVBoxLayout()
        self._init_entry_layout(layout_entry)
        layout_plots = QVBoxLayout()
        self._init_plot_layout(layout_plots)
        main_layout.addLayout(layout_entry,1)
        main_layout.addLayout(layout_plots,3)

        return main_layout

    def _init_entry_layout(self, main_layout: QVBoxLayout):
        # --- Group 0: General & Antenna Settings ---
        grp_antenna = QGroupBox("Antenna Config")
        form_antenna = QFormLayout()

        self.spin_elements = QSpinBox()
        self.spin_elements.setRange(1, 128)
        self.spin_elements.setValue(8)  # Default: num_antenna_elements=8

        self.sll_db = QLineEdit("25")
        self.sll_db.setPlaceholderText("e.g. 25dB (negative)")

        self.txt_disconnected = QLineEdit("8")  # Default: disconnected_elements=[8]
        self.txt_disconnected.setPlaceholderText("e.g. 8 or 7, 8")

        self.aux_gain_db= QLineEdit("0")  # Default: disconnected_elements=[8]
        self.aux_gain_db.setPlaceholderText("e.g. 0dB")

        self.main_pattern_weight = QComboBox()
        self.main_pattern_weight.addItem("Conventional", userData="ula")
        self.main_pattern_weight.addItem("Taylor", userData="taylor")
        self.main_pattern_weight.addItem("Chebyshev", userData="cheby")

        self.main_antenna_order = QSpinBox()
        self.main_antenna_order.setRange(2, 128)
        self.main_antenna_order.setValue(10)

        form_antenna.addRow("Number of Aux Elements:", self.spin_elements)
        form_antenna.addRow("Disconnected Elements:", self.txt_disconnected)
        form_antenna.addRow("Antenna Weighting:", self.main_pattern_weight)
        form_antenna.addRow("Antenna Order:", self.main_antenna_order)
        form_antenna.addRow("Sidelobe Level (dB):", self.sll_db)
        form_antenna.addRow("Aux Channel Gain (dB):", self.aux_gain_db)
        grp_antenna.setLayout(form_antenna)

        # --- Group 1: Target Signal Settings ---
        grp_target = QGroupBox("Target Config")
        form_target = QFormLayout()

        self.chk_tgt_on = QCheckBox()
        self.chk_tgt_on.setChecked(True)  # Default: tgt_on=True

        self.tgt_sig_type = QComboBox()
        self.tgt_sig_type.addItem("LFM", userData="lfm")
        self.tgt_sig_type.addItem("Barker-13", userData="barker_13")
        self.tgt_sig_type.addItem("CW", userData="cw")
        self.tgt_sig_type.addItem("Noise", userData="noise")

        self.tgt_gate = QLineEdit("0.4, 0.6")
        self.tgt_gate.setPlaceholderText("Comma-separated Gate (Gate Fraction)")

        self.tgt_timebandwidth_db = QLineEdit("10")
        self.tgt_timebandwidth_db.setPlaceholderText("e.g. 10 (dB)")

        form_target.addRow("Target On:", self.chk_tgt_on)
        form_target.addRow("Signal Type:", self.tgt_sig_type)
        form_target.addRow("Fractional Gate:", self.tgt_gate)
        form_target.addRow("Time-Bandwidth Product (dB)", self.tgt_timebandwidth_db)
        grp_target.setLayout(form_target)

        # --- Group 2: Jammer Signal Settings ---
        grp_jammers = QGroupBox("Jammer Configuration")
        form_jammers = QFormLayout()

        self.spin_num_jammers = QSpinBox()
        self.spin_num_jammers.setRange(0, 32)
        self.spin_num_jammers.setValue(5)  # Default: num_jammers=5

        self.txt_jam_snrs = QLineEdit("30, 10, 5, 0, 3, 8, 1")
        self.txt_jam_snrs.setPlaceholderText("Comma-separated SNRs (dB)")

        self.txt_doas = QLineEdit("15.0, -26.0, 33.0, -33.0, 25.0, 10.0, -15.0")
        self.txt_doas.setPlaceholderText("Comma-separated DOAs (degrees)")

        self.txt_bw_range = QLineEdit("0.5, 0.5")  # Default: jam_bw_range=[0.5, 0.5]

        form_jammers.addRow("Number of Jammers:", self.spin_num_jammers)
        form_jammers.addRow("Jammer SNRs (dB):", self.txt_jam_snrs)
        form_jammers.addRow("Jammer DOAs (deg):", self.txt_doas)
        form_jammers.addRow("Jammer BW Range:", self.txt_bw_range)
        grp_jammers.setLayout(form_jammers)

        # --- Group 3: Gating Range Settings ---
        grp_gating = QGroupBox("Gating Ranges")
        form_gating = QFormLayout()

        self.txt_min_gate = QLineEdit("0.2, 0.2")  # Default: min_gate_range_jammer=[0.2, 0.2]
        self.txt_max_gate = QLineEdit("0.8, 0.8")  # Default: max_gate_range_jammer=[0.8, 0.8]

        form_gating.addRow("Min Gate Range:", self.txt_min_gate)
        form_gating.addRow("Max Gate Range:", self.txt_max_gate)
        grp_gating.setLayout(form_gating)

        # --- Submit Button ---
        self.btn_run = QPushButton("Run Simulation")
        self.btn_run.clicked.connect(self._on_run_clicked)
        self.btn_preview = QPushButton("Preview Simulation")
        self.btn_preview.clicked.connect(self._on_preview_clicked)

        main_layout.addWidget(grp_antenna)
        main_layout.addWidget(grp_target)
        main_layout.addWidget(grp_jammers)
        main_layout.addWidget(grp_gating)
        main_layout.addWidget(self.btn_preview)
        main_layout.addWidget(self.btn_run)
        main_layout.addStretch()

    def _init_plot_layout(self, layout:QVBoxLayout):
        mosaic_layout = [["spatial_plot", "."],
                         ["time_plot", "dynamic_range"]]
        self.axes = self.figure.subplot_mosaic(mosaic_layout)
        for name, ax in self.axes.items():
            ax.set_title(name)
        self.canvas = FigureCanvas(self.figure)

        layout.addWidget(self.canvas)

    def _parse_floats(self, text: str) -> list:
        if not text.strip():
            return []
        tokens = re.split(r'[\s,]+', text.strip())
        return [float(x) for x in tokens if x != ""]

    def _parse_ints(self, text: str) -> list:
        if not text.strip():
            return []
        tokens = re.split(r'[\s,]+', text.strip())
        return [int(x) for x in tokens if x != ""]

    ################### Figures #####################################
    def _draw_plots(self):
        self.canvas.draw()

    def _update_antenna_preview(self, pattern_responses, az_points, pattern_labels, doas):
        ax = self.axes["spatial_plot"]
        ax.clear()
        N, L = np.shape(pattern_responses) #N elements
        D = len(doas)
        print(f"number of responses: {N}")
        for i in range(N):
            pat = np.squeeze(pattern_responses[i,:])
            ax.plot(az_points, pat, label=pattern_labels[i])

        ylim = (-50, np.max(pattern_responses.all()))
        for d in range(D):
            doa = doas[d]
            ax.plot([doa, doa], [ylim[0]-10, ylim[1]+10], "r--", label=f"Jammer {d}")


        ax.grid(True)
        ax.legend()
        ax.set_xlabel("Azimuth [deg]")
        ax.set_ylabel("Power [dB]")
        ax.set_ylim(ylim)



    ################### Events ######################################
    def _on_preview_clicked(self):
        try:
            params = {
                "num_jammers": self.spin_num_jammers.value(),
                "num_antenna_elements": self.spin_elements.value(),
                "disconnected_elements": self._parse_ints(self.txt_disconnected.text()),
                "main_order": self.main_antenna_order.value(),

                "tgt_on": self.chk_tgt_on.isChecked(),

                "jam_SNRs": self._parse_floats(self.txt_jam_snrs.text()),
                "jam_bw_range": self._parse_floats(self.txt_bw_range.text()),
                "doas": self._parse_floats(self.txt_doas.text()),
                "min_gate_range_jammer": self._parse_floats(self.txt_min_gate.text()),
                "max_gate_range_jammer": self._parse_floats(self.txt_max_gate.text()),
            }

            # Emit parsed dictionary to Controller
            self.preview_requested.emit(params)

        except ValueError as e:
            QMessageBox.critical(
                self,
                "Parsing Error",
                f"Invalid numerical entry in form fields.\nDetails: {e}"
            )

    def _on_run_clicked(self):
        try:
            params = {
                "tgt_on": self.chk_tgt_on.isChecked(),
                "num_jammers": self.spin_num_jammers.value(),
                "num_antenna_elements": self.spin_elements.value(),
                "jam_SNRs": self._parse_floats(self.txt_jam_snrs.text()),
                "jam_bw_range": self._parse_floats(self.txt_bw_range.text()),
                "doas": self._parse_floats(self.txt_doas.text()),
                "min_gate_range_jammer": self._parse_floats(self.txt_min_gate.text()),
                "max_gate_range_jammer": self._parse_floats(self.txt_max_gate.text()),
                "disconnected_elements": self._parse_ints(self.txt_disconnected.text()),
            }

            # Emit parsed dictionary to Controller
            self.simulation_requested.emit(params)

        except ValueError as e:
            QMessageBox.critical(
                self,
                "Parsing Error",
                f"Invalid numerical entry in form fields.\nDetails: {e}"
            )


# Example usage inside Controller
if __name__ == "__main__":
    app = create_app()
    win = init_view()
    from core.antennas.array import ElementPatterns
    from core.antennas.classic.ULA import ULA

    def handle_preview(params: dict):
        print(f"plotting preview scenario:")
        for k, v in params.items():
            print(f"\t{k}: {v}")

        ssl_taylor = 25
        num_antenna_elements = params["num_antenna_elements"]
        main_order = params["main_order"]
        # make antenna for spatial response plot
        antenna = ULA(num_elements=num_antenna_elements)
        patterns = ([ElementPatterns.taylor_subarray(num_sub_elements=main_order, sll_db=ssl_taylor)]
                    + [ElementPatterns.delta_subarray(4, gain_offset=(-ssl_taylor + 3))] * (num_antenna_elements - 1))
        antenna.set_disconnected_elements(params["disconnected_elements"])
        antenna.set_patterns(patterns)

        doas = params["doas"]
        pattern_resp_names = ["main", "aux_0", "aux_1", "aux_2", "aux_3", "aux_4", "aux_5", "aux_6", "aux_7", "aux_8", "aux_9"]
        az_points, pattern_resp = antenna.element_pattern_response()
        win._update_antenna_preview(pattern_responses=pattern_resp, az_points=az_points, pattern_labels=pattern_resp_names, doas=doas)
        win._draw_plots()


    def handle_simulation(params: dict):
        print("Executing multiple_jammer_case_with_adc with params:")
        for k, v in params.items():
            print(f"  {k}: {v}")

        # Unpack directly into your function:
        # input_sigs, mixed_sigs, antenna, adc = multiple_jammer_case_with_adc(**params)


    win.simulation_requested.connect(handle_simulation)
    win.preview_requested.connect(handle_preview)
    run_window_as_app(win=win)

