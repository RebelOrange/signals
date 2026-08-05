from abc import ABC, abstractmethod
import numpy as np
from core.antennas.van_trees.array_math import *
from scipy.constants import c

class AntennaArray:
    def __init__(self, positions, wavelength=1.0, element_pattern=None, mixer = None):
        self.positions = positions
        self.wavelength = wavelength
        self.element_pattern = element_pattern
        self.mixer = mixer

        self.X = None
        self.A = None
        self.weights = np.ones((self.num_elements, 1)) / self.num_elements
        self.channel_noise = None
        self.channel_noise_var = 0

    @property
    def num_elements(self):
        return self.positions.shape[1]

    def set_ktb_variance(self, ktb_var):
        self.ktb_var = ktb_var

    def manifold_vector(self, doa):
        return manifold_vector_doa(
            az=doa[0], el=doa[1],
            positions=self.positions,
            wavelength=self.wavelength
        )

    def mixing_matrix(self, doas):
        return np.column_stack([
            self.manifold_vector(doa) for doa in doas
        ])

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
            self.channel_noise[m, :] = np.sqrt(ktb_var) * (np.random.normal(0, 1, L) + 1j * np.random.normal(0, 1, L))

        self.X_n = self.X + self.channel_noise

    def receive(self, signals: list, doas: list[tuple[float, float]], ktb_var: float = 0):

        A = self.mixing_matrix(doas)
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

    def scan_response_weights(self, weights=None):
        w = self.weights if weights is None else weights
        return scan_response_weights(
            w=w,
            positions=self.positions,
            wavelength=self.wavelength,
        )