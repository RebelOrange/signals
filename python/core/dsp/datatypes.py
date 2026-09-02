from dataclasses import dataclass, field
from typing import Any, List
import numpy as np

@dataclass
class SignalEvent:
    """Metadata for a gated sig gen emission"""
    start_time: float
    duration: float
    start_idx: int
    end_idx: int
    label: str
    waveform_config: Any
    pulse_iq: np.ndarray



@dataclass
class TimeGate:
    start_time: float
    stop_time: float
    @property
    def duration(self):
        return self.stop_time - self.start_time


@dataclass
class PulsedSignalConfig:
    gate: TimeGate
    waveform_config: Any
    #TODO: Add N pulses and duty cycle?

@dataclass
class TimeGrid:
    sample_rate: float
    duration: float
