from dataclasses import fields, MISSING
from typing import Type, Any
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
)

from core.dsp.signal_generators.signal_providers.PSK import BPSKConfig


class DynamicConfigDialog(QDialog):
    """Generates a dynamic PyQt form for any Python dataclass."""

    def __init__(self, config_cls: Type[Any], current_config: Any = None, parent=None):
        super().__init__(parent)
        self.config_cls = config_cls
        self.created_config = None
        self.inputs = {}

        self.setWindowTitle(f"Configure {config_cls.__name__}")
        self.resize(350, 300)

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Iterate over all dataclass fields dynamically
        for field_info in fields(config_cls):
            field_name = field_info.name

            # Determine initial value (from existing instance or default)
            if current_config and hasattr(current_config, field_name):
                val = getattr(current_config, field_name)
            elif field_info.default is not MISSING:
                val = field_info.default
            else:
                val = ""

            val_str = "" if val is None else str(val)

            # Create input widget
            line_edit = QLineEdit(val_str)
            line_edit.setPlaceholderText("None" if "Optional" in str(field_info.type) else "Required")

            label_text = field_name.replace("_", " ").title()
            form_layout.addRow(f"{label_text}:", line_edit)

            self.inputs[field_name] = line_edit

        main_layout.addLayout(form_layout)

        btn_save = QPushButton("Save Configuration")
        btn_save.clicked.connect(self._on_save)
        main_layout.addWidget(btn_save)

    def _on_save(self):
        kwargs = {}
        for field_info in fields(self.config_cls):
            raw_text = self.inputs[field_info.name].text().strip()

            # Parse None / empty values vs floats
            if not raw_text or raw_text.lower() == "none":
                kwargs[field_info.name] = None
            else:
                try:
                    kwargs[field_info.name] = float(raw_text)
                except ValueError:
                    QMessageBox.critical(self, "Type Error", f"Field '{field_info.name}' must be numeric.")
                    return

        try:
            # Instantiating the class executes __post_init__ validation automatically
            self.created_config = self.config_cls(**kwargs)
            self.accept()
        except Exception as e:
            # Catches errors like LFMConfig's invalid frequency parameter combinations
            QMessageBox.critical(self, "Validation Error", str(e))





if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QComboBox, QPushButton
    from core.dsp.signal_generators.signal_providers.CW import CwConfig
    from core.dsp.signal_generators.signal_providers.FM import LFMConfig
    from core.dsp.signal_generators.signal_providers.PSK import BPSKConfig, CodeConstructer


    # Import your dataclasses
    # from configs.cw import CwConfig
    # from configs.lfm import LFMConfig

    class SignalSetupWidget(QWidget):
        # Registry mapping GUI selection strings to actual dataclasses
        CONFIG_MAP = {
            "CW": CwConfig,
            "LFM": LFMConfig,
            "BPSK": BPSKConfig,
        }

        def __init__(self):
            super().__init__()
            self.setWindowTitle("Signal Configuration View")
            self.active_config = None

            layout = QHBoxLayout(self)

            # 1. ComboBox for signal selection
            self.combo_signal = QComboBox()
            self.combo_signal.addItems(self.CONFIG_MAP.keys())

            # 2. Configure Button
            self.btn_configure = QPushButton("Configure Signal")
            self.btn_configure.clicked.connect(self._open_config_dialog)

            layout.addWidget(self.combo_signal)
            layout.addWidget(self.btn_configure)

        def _open_config_dialog(self):
            selected_key = self.combo_signal.currentText()
            config_cls = self.CONFIG_MAP[selected_key]

            # Reuse current config if it matches the selected type
            current = self.active_config if isinstance(self.active_config, config_cls) else None

            dialog = DynamicConfigDialog(config_cls, current_config=current, parent=self)
            if dialog.exec_():
                self.active_config = dialog.created_config
                print(f"Successfully created {selected_key} Config object:")
                print(self.active_config)

    app = QApplication(sys.argv)
    view = SignalSetupWidget()
    view.show()
    sys.exit(app.exec_())