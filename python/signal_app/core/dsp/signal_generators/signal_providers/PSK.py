from email.policy import default
from typing import Optional, List

import numpy as np
from dataclasses import dataclass

from .registry import register_provider

@dataclass(frozen=True)
class CodeConstructer:

    @staticmethod
    def barker(order:int = 13):
        match order:
            case 13:
                return [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, -1, 1, 1]
            case _:
                raise ValueError("Barker code must be known.")


@dataclass
class BPSKConfig:
    code: List[int]
    frequency: float

    chip_width: Optional[float] = None
    amplitude: Optional[float] = 1
    phase: Optional[float] = 0


@register_provider(BPSKConfig)
class BPSKProvider:
    def __init__(self, config: BPSKConfig):
        self._config = config

    def generate_iq(self, time_vector) -> np.ndarray:
        f_0 = self._config.frequency
        phase_offset = self._config.phase
        amp = self._config.amplitude
        Ts = time_vector[1] - time_vector[0]
        Fs = 1/Ts

        chip_width = self._config.chip_width
        code = np.asarray(self._config.code,dtype=float)
        duration = time_vector[-1] - time_vector[0]

        if len(code) == 0:
            raise ValueError("config.code must contain at least one chip.")

        if chip_width is not None:
            samples_per_chip = int(round(chip_width * Fs))

            if samples_per_chip < 1:
                raise ValueError("bpsk_chip_width is too small for the configured sample_rate.")

            N = len(code) * samples_per_chip
            min_num_samples = N
        else:
            # fit the whole code into the pulsewidth
            N = len(time_vector)
            chip_width = duration/len(code)
            samples_per_chip = int(np.ceil(chip_width * Fs))


        baseband_code = np.repeat(code, samples_per_chip)
        if len(baseband_code) > N:
            baseband_code = baseband_code[:N]

        duration = N * Ts
        t = time_vector

        if len(t) > N:
            t = t[:N]
        elif len(t) < N:
            t = np.arange(N) * Ts

        carrier = np.exp(1j * (2 * np.pi * f_0 * t + phase_offset))
        x = amp * baseband_code * carrier
        return x
