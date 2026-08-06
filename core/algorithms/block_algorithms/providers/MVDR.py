from typing import Optional

import numpy as np
from dataclasses import dataclass

from .registry import register_provider


@dataclass
class CwConfig:
    frequency: float

    amplitude: Optional[float] = 1
    phase: Optional[float] = 0


@register_provider(CwConfig)
class CwProvider:
    def __init__(self, config: CwConfig):
        self._config = config

    def generate_iq(self, time_vector) -> np.ndarray:
        f_0 = self._config.frequency
        phi = self._config.phase
        amp = self._config.amplitude
        x = amp*np.exp(1j*(2*np.pi*f_0*time_vector+phi))
        return x
