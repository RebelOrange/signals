from abc import ABC, abstractmethod
import numpy as np
from core.antennas.van_trees.array_math import *
from scipy.constants import c
import scipy.signal.windows as windows

class ElementPatterns:
    """Helper strategies for individual antenna element radiation patterns."""

    @staticmethod
    def omni():
        """Omnidirectional pattern (1.0 gain in all directions)."""
        return lambda az, el: 1.0

    @staticmethod
    def taylor_subarray(
            num_sub_elements: int = 20,
            sll_db: float = 30.0,
            d_over_lambda: float = 0.5,
            normalize: bool = True,
            gain_offset: float = 0.0,
    ):
        """Generates a Taylor subarray pattern.

        If normalize=True, peak mainbeam gain is scaled to 1.0 (0 dB).
        """
        sub_weights = windows.taylor(num_sub_elements, nbar=4, sll=sll_db)
        sub_pos = (
                          np.arange(num_sub_elements) - (num_sub_elements - 1) / 2.0
                  ) * d_over_lambda

        # Peak gain of Taylor subarray occurs at broadside (sum of weights)
        peak_gain = np.sum(sub_weights) if normalize else 1.0

        peak_gain = peak_gain/(10**(gain_offset/20.0))

        def pattern(az: float, el: float) -> complex:
            u = np.sin(np.radians(az)) * np.cos(np.radians(el))
            af = np.sum(sub_weights * np.exp(1j * 2 * np.pi * sub_pos * u))
            return af / peak_gain

        return pattern

    @staticmethod
    def delta_subarray(
            num_sub_elements: int = 20,
            d_over_lambda: float = 0.5,
            normalize: bool = True,
            gain_offset: float = 0.0,
    ):
        """Generates a monopulse Delta subarray pattern.

        If normalize=True, peak lobe gain is scaled to 1.0 (0 dB).
        """
        sub_weights = np.ones(num_sub_elements, dtype=complex)
        sub_weights[num_sub_elements // 2:] = -1.0  # Phase flip
        sub_pos = (
                          np.arange(num_sub_elements) - (num_sub_elements - 1) / 2.0
                  ) * d_over_lambda

        # Find peak gain across spatial domain for Delta pattern
        if normalize:
            u_grid = np.sin(np.radians(np.linspace(-90, 90, 1000)))
            peak_gain = np.max(
                [
                    np.abs(
                        np.sum(sub_weights * np.exp(1j * 2 * np.pi * sub_pos * u))
                    )
                    for u in u_grid
                ]
            )
        else:
            peak_gain = 1.0

        peak_gain = peak_gain/(10**(gain_offset/20.0))
        def pattern(az: float, el: float) -> complex:
            u = np.sin(np.radians(az)) * np.cos(np.radians(el))
            af = np.sum(sub_weights * np.exp(1j * 2 * np.pi * sub_pos * u))
            return af / peak_gain

        return pattern

    @staticmethod
    def cosine(q: float = 1.0, azimuth_offset_deg: float = 0.0):
        """
        Cosine pattern centered at a specific azimuth direction.
        gain = cos^q(az - offset) * cos^q(el)
        """

        def pattern(az: float, el: float):
            rel_az = az - azimuth_offset_deg
            if -90 <= rel_az <= 90 and -90 <= el <= 90:
                az_rad, el_rad = np.radians(rel_az), np.radians(el)
                return (np.cos(az_rad) ** q) * (np.cos(el_rad) ** q)
            return 0.0

        return pattern

class AntennaArray:
    def __init__(self, positions, wavelength=1.0, element_pattern=None, mixer=None):
        self.positions = positions
        self.wavelength = wavelength
        self.mixer = mixer
        self.set_patterns(element_pattern=element_pattern)
        self.X = None
        self.A = None
        self.doas = None
        self.weights = np.ones((self.num_elements, 1), dtype=complex) / self.num_elements
        self.channel_noise = None
        self.channel_noise_var = 0

    def set_patterns(self, element_pattern):
        """
        Sets or updates element patterns post-initialization.

        Args:
            element_pattern:
                - None: Defaults all elements to Omnidirectional.
                - Callable: Applies the same pattern function to ALL elements.
                - List/Tuple of Callables: Applies individual patterns per element (length must equal N).
        """
        if element_pattern is None:
            self.element_patterns = [ElementPatterns.omni()] * self.num_elements
        elif callable(element_pattern):
            self.element_patterns = [element_pattern] * self.num_elements
        elif isinstance(element_pattern, (list, tuple)):
            if len(element_pattern) != self.num_elements:
                raise ValueError(
                    f"Length of element_pattern list ({len(element_pattern)}) "
                    f"must match number of array elements ({self.num_elements})."
                )
            self.element_patterns = list(element_pattern)
        else:
            raise TypeError("element_pattern must be None, a callable, or a list of callables.")

    def set_disconnected_elements(self, indices: list[int] | set[int]) -> None:
        """Disconnects specified antenna elements by index.

        Disconnected elements receive 0 RF signal power from the environment,
        simulating a 50-ohm load termination, but still generate kTB thermal noise.
        """
        # Validate indices
        valid_indices = {
            i for i in indices if 0 <= i < self.num_elements
        }
        self.disconnected_elements = valid_indices

    @property
    def num_elements(self):
        return self.positions.shape[1]

    def set_ktb_variance(self, ktb_var):
        self.ktb_var = ktb_var

    def manifold_vector(self, doa):
        """
        Calculates steering vector for a given DOA tuple (az, el).
        Evaluates each element's individual gain response at (az, el).
        """
        # 1. Spatial phase propagation across array positions (N, 1)
        v = manifold_vector_doa(
            az=doa[0], el=doa[1],
            positions=self.positions,
            wavelength=self.wavelength
        ).reshape(-1, 1)

        # 2. Evaluate each element's unique pattern response at this (az, el)
        gains = np.array([
            [pattern(doa[0], doa[1])] for pattern in self.element_patterns
        ], dtype=complex)

        # 3. Element-wise product of spatial phase and individual element gains
        return v * gains

    def mixing_matrix(self, doas, ktb_var:float = 0.0):
        A = np.column_stack([self.manifold_vector(doa) for doa in doas])

        # Zero out rows for disconnected elements across all DOAs

        if hasattr(self, "disconnected_elements") and self.disconnected_elements:
            for ch_idx in self.disconnected_elements:
                A[ch_idx, :] = 0.0
        N = ones_like(A)*ktb_var
        self.A_n = A+N
        return A

    def signals_matrix(self, signals_list: list[np.ndarray]):
        return np.vstack(signals_list)

    def add_channel_noise(self, channel_noise_var):
        self.channel_noise = np.zeros_like(self.X, dtype=np.complex128)
        if channel_noise_var > 0:
            self.channel_noise_var = channel_noise_var
        ktb_var = self.channel_noise_var
        print(ktb_var)
        M, L = self.X.shape
        for m in range(M):
            self.channel_noise[m, :] = np.sqrt(ktb_var/2) * (np.random.normal(0, 1, L) + 1j * np.random.normal(0, 1, L))

        self.X_n = self.X + self.channel_noise

    def receive(self, signals: list, doas: list[tuple[float, float]], ktb_var: float = 0):
        self.doas = doas
        A = self.mixing_matrix(doas, ktb_var)
        self.A = A
        if self.mixer is not None and hasattr(self.mixer, 'set_mixing_matrix') and hasattr(self.mixer, 'mix_signals'):
            self.mixer.set_mixing_matrix(self.A)

            if len(signals) > 0 and hasattr(signals[0], 'iq') and hasattr(signals[0],'__class__'):
                SignalClass = signals[0].__class__
                # mixer exists and input is a signal list
                rx_sigs:list = self.mixer.mix_signals(signals)
                self.X = self.mixer.Y # result of mixing matrix
                self.add_channel_noise(ktb_var)

                # set iq to be the same as antenna
                for idx, sig in enumerate(rx_sigs):
                    sig.iq = self.X_n[idx,:]

                return rx_sigs

            # if signals list is not a signal_class, just return default data matrix without mixer
            else:
                D = self.signals_matrix(signals)
                self.X = A @ D

                # generate channel thermal noise
                # check for channel noise on input
                self.add_channel_noise(ktb_var)

                return self.X
        else:
            D = self.signals_matrix(signals)
            self.X = A @ D

            # generate channel thermal noise
            # check for channel noise on input
            self.add_channel_noise(ktb_var)

            return self.X



    def set_weights(self, weights):
        self.weights = weights

    def steer(self, doa, normalize=True):
        w = self.manifold_vector(doa)
        if normalize:
            w = w / self.num_elements
        self.set_weights(w)
        return w

    def beamform_output(self, weights=None):
        if self.X is None:
            raise ValueError("No received data. Call receive() first.")

        w = self.weights if weights is None else weights
        return w.conj().T @ self.X

    def beamform(self, steering_doa=None, weights=None):
        if weights is not None:
            self.set_weights(weights)
        elif steering_doa is not None:
            self.steer(steering_doa)

        return np.squeeze(self.beamform_output())

    @property
    def covariance_matrix(self):
        if self.X is None:
            raise ValueError("No received data. Call receive() first.")
        return sample_covariance_matrix(self.X)

    def scan_response(self):
        return scan_response_datamatrix(X=self.X, positions=self.positions, wavelength=self.wavelength)

    def scan_response_weights(self, weights=None, angle_resolution: float = 0.5, normalize: bool = True):
        w = self.weights if weights is None else weights
        scan_angles = np.arange(-90, 90, angle_resolution)
        scan_powers = np.zeros(len(scan_angles))

        for idx, phi in enumerate(scan_angles):
            # 1. Use self.manifold_vector to include custom per-element patterns
            v = self.manifold_vector((phi, 0.0))

            # 2. Compute Array Factor output magnitude |w^H * v|
            scan_power = np.abs(w.conj().T @ v).squeeze()
            scan_powers[idx] = scan_power

        # 3. Prevent log10(0) warnings
        eps = 1e-12
        if normalize and np.max(scan_powers) > 0:
            scan_powers = scan_powers / np.max(scan_powers)

        return scan_angles, 20 * np.log10(scan_powers + eps)

    def element_pattern_response(self, az_grid=None, el: float = 0.0, db: bool = True):
        if az_grid is None:
            az_grid = np.linspace(-90, 90, 722)

        num_angles = len(az_grid)
        element_powers = np.zeros((self.num_elements, num_angles))
        for j, pat in enumerate(self.element_patterns):
            for i, az in enumerate(az_grid):
                element_powers[j,i] = np.abs(pat(az, el))

        if db:
            element_powers = 20*np.log10(element_powers)

        return az_grid, element_powers

    def element_scan_responses_datamatrix(self, az_grid=None, el: float = 0.0, db: bool = True):
        """
        Calculates the scan response (power vs azimuth) for each individual element
        in the array based on the received data matrix X.

        Args:
            az_grid: 1D array of azimuth angles in degrees (default: -90 to +90 in 1 deg steps).
            el: Elevation angle in degrees (default: 0.0).
            db: If True, returns normalized power in dB. If False, returns linear power.

        Returns:
            az_grid: 1D array of scan angles (shape: num_angles,).
            element_powers: 2D array of individual element power responses (shape: num_elements, num_angles).
        """
        if self.X_n is None:
            raise ValueError("No received data. Call receive() first.")

        if az_grid is None:
            az_grid = np.linspace(-90, 90, 722)

        num_angles = len(az_grid)
        element_powers = np.zeros((self.num_elements, num_angles))

        # Evaluate individual element responses across scan angles
        for i, az in enumerate(az_grid):
            # Manifold vector a(az, el) of shape (N, 1) incorporating individual element patterns
            a = self.manifold_vector((az, el))

            # Element-wise response: y_m(t) = conj(a_m) * X_m(t) -> shape (N, num_samples)
            y_element = a.conj() * self.X_n

            # Mean power for each element at this scan angle
            element_powers[:, i] = np.mean(np.abs(y_element) ** 2, axis=1)

        if db:
            eps = 1e-12
            max_val = np.max(element_powers)
            if max_val > 0:
                element_powers = 10 * np.log10(element_powers / max_val + eps)
            else:
                element_powers = 10 * np.log10(element_powers + eps)

        return az_grid, element_powers