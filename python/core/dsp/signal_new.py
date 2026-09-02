import numpy as np
from dataclasses import dataclass, field
from scipy import signal as scipy_signal
from typing import List, Any
import pandas as pd

from .datatypes import SignalEvent

@dataclass
class Signal:
    iq: np.ndarray
    sample_rate: float
    events: List[SignalEvent] = field(default_factory=list)
    label: str = "Unlabeled"

    @property
    def duration(self) -> float:
        return self.num_samples / self.sample_rate

    @property
    def fs(self) -> float:
        return self.sample_rate

    @property
    def time_vector(self) -> np.ndarray:
        return self.t

    @property
    def dT(self) -> float:
        return 1/self.sample_rate

    @property
    def num_samples(self) -> int:
        return len(self.iq)

    @property
    def t(self):
        return np.linspace(0, self.duration, self.num_samples)

    import pandas as pd
    import numpy as np

    def save_to_csv(self, file_path: str):
        """
        Saves the signal's I/Q data and events to a CSV file with metadata.
        Event metadata in the header is column-aligned above each event's I/Q data.
        """
        df = pd.DataFrame({'I': self.iq.real, 'Q': self.iq.imag})

        # Base rows for signal metadata (Col 0 and Col 1)
        row_label = ["# Label", str(self.label)]
        row_sample_rate = ["# Sample Rate", str(self.sample_rate)]
        row_event_info = ["# Event Start/End", ""]

        for i, event in enumerate(self.events):
            pulse = event.pulse_iq

            # 1. Align event metadata directly above event I/Q columns
            row_label.extend([f"Event {i} Label", f"'{event.label}'"])
            row_sample_rate.extend(["Start Index", str(event.start_idx)])
            row_event_info.extend(["End Index", str(event.end_idx)])

            # 2. Build event I/Q columns
            event_i_col = np.full(self.num_samples, np.nan)
            event_q_col = np.full(self.num_samples, np.nan)

            # Time-align pulse placement (or use 0:len(pulse) if relative alignment is intended)
            start, end = event.start_idx, event.end_idx
            event_i_col[0:len(pulse)] = pulse.real
            event_q_col[0:len(pulse)] = pulse.imag

            df[f'{event.label}_{i}_I'] = event_i_col
            df[f'{event.label}_{i}_Q'] = event_q_col

        # Format header lines with comma separation
        header_lines = [
            ",".join(row_label) + "\n",
            ",".join(row_sample_rate) + "\n",
            ",".join(row_event_info) + "\n"
        ]

        # Write header followed by dataframe
        with open(file_path, 'w') as f:
            f.writelines(header_lines)
            df.to_csv(f, index=False)