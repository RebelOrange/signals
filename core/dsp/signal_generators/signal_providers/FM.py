from typing import Optional

import numpy as np
from dataclasses import dataclass

from .registry import register_provider


@dataclass
class LFMConfig:
    pulse_width: Optional[float] = 0

    phase: Optional[float] = 0
    amplitude: Optional[float] = 1
    frequency_lower: Optional[float]=None
    frequency_upper: Optional[float]=None
    frequency_center: Optional[float]=None
    chirp_bandwidth: Optional[float]=None

    def __post_init__(self):
        bounds_given = self.frequency_lower is not None and self.frequency_upper is not None
        center_bw_given = self.frequency_center is not None and self.chirp_bandwidth is not None
        if bounds_given and center_bw_given:
            raise ValueError("Both frequency bounds and chirp bandwidth are defined, "
                             "specify either (frequency_lower, frequency_upper) or (frequency_center, chirp_bandwidth)")

        if bounds_given:
            self.chirp_bandwidth = self.frequency_upper - self.frequency_lower
            self.frequency_center = (self.frequency_upper + self.frequency_lower) / 2
        elif center_bw_given:
            self.frequency_lower = self.frequency_center - (self.chirp_bandwidth / 2)
            self.frequency_upper = self.frequency_center + (self.chirp_bandwidth / 2)
        else:
            raise ValueError("Incomplete configuration, specify (frequency_lower, frequency_upper) or"
                             "(frequency_center, chirp_bandwidth) ")


@register_provider(LFMConfig)
class LFMProvider:
    def __init__(self, config: LFMConfig):
        self._config = config

    def generate_iq(self, time_vector:np.ndarray) -> np.ndarray:
        f_l = self._config.frequency_lower
        f_u = self._config.frequency_upper
        amp = self._config.amplitude
        BW = self._config.chirp_bandwidth
        tau = self._config.pulse_width
        phi = self._config.phase
        t = time_vector
        f0 = self._config.frequency_lower

        # Construct LFM
        k = BW/(t[-1]-t[0])

        phase_lfm = 2*np.pi*(f0 * t + 0.5*k*(t**2)) +phi
        return amp * np.exp(1j*phase_lfm)