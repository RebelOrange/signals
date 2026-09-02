from typing import Optional

import numpy as np
from dataclasses import dataclass

from .registry import register_provider


@dataclass
class NoiseConfig:
    frequency_lower: Optional[float]=None
    frequency_upper: Optional[float]=None
    frequency_center: Optional[float]=None
    bandwidth: Optional[float]=None
    variance: Optional[float] = 1

    def __post_init__(self):
        bounds_given = self.frequency_lower is not None and self.frequency_upper is not None
        center_bw_given = self.frequency_center is not None and self.bandwidth is not None
        if bounds_given and center_bw_given:
            raise ValueError("Both frequency bounds and chirp bandwidth are defined, "
                             "specify either (frequency_lower, frequency_upper) or (frequency_center, chirp_bandwidth)")

        if bounds_given:
            self.bandwidth = self.frequency_upper - self.frequency_lower
            self.frequency_center = (self.frequency_upper + self.frequency_lower) / 2
        elif center_bw_given:
            self.frequency_lower = self.frequency_center - (self.bandwidth / 2)
            self.frequency_upper = self.frequency_center + (self.bandwidth / 2)
        else:
            raise ValueError("Incomplete configuration, specify (frequency_lower, frequency_upper) or"
                             "(frequency_center, chirp_bandwidth) ")



@register_provider(NoiseConfig)
class NoiseProvider:
    def __init__(self, config: NoiseConfig):
        self._config = config

    def generate_iq(self, time_vector) -> np.ndarray:
        t = time_vector
        Ts = t[1]-t[0]
        duration = t[-1] - t[0]
        Fs = 1/Ts
        N = len(t)
        f_l = self._config.frequency_lower
        f_u = self._config.frequency_upper
        var = self._config.variance

        N_fft = int(2 ** (int(np.ceil(np.log2(N))) + 2))

        # 2. Get frequency bins
        freqs = np.fft.fftfreq(N_fft, d=Ts)

        # 3. Create a mask for frequencies within [f_lower, f_upper]
        band_mask = (freqs >= f_l) & (freqs <= f_u)
        num_active_bins = np.sum(band_mask)

        # Handle edge case where requested band contains no bins
        if num_active_bins == 0:
            closest_bin = np.argmin(np.abs(freqs - (f_l + f_u) / 2))
            band_mask[closest_bin] = True
            num_active_bins = 1

        # 4. Generate frequency-domain complex white noise (flat spectrum)
        spectrum = np.zeros(N_fft, dtype=np.complex128)
        phases = np.random.uniform(0, 2 * np.pi, size=num_active_bins)
        spectrum[band_mask] = np.exp(1j * phases)

        # 5. Transform to time domain
        x_full = np.fft.ifft(spectrum)

        x =  x_full[:N]

        # Scale to variance to desired noise power
        des_var = var
        var = np.dot(x, x.conj()) / len(x)
        print(f"Generated noise with variance {var.real:0.5f}, requested variance {des_var.real:0.2f}")
        scale_factor = des_var.real / var.real
        print(f"Scaled noise with factor {scale_factor:0.2f}")
        x *= np.sqrt(scale_factor)
        new_var = np.dot(x, x.conj()) / len(x)
        print(f"New noise variance {new_var.real:0.2f}")
        return x
