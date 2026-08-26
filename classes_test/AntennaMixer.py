from json.decoder import scanstring

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import matplotlib

from classes_test.Mixer import Mixer


from typing import List, Union, Tuple
from classes_test.ComplexSignal import ComplexSignal
from scipy.signal.windows import taylor

from classes_test.Beamformer import Beamformer as beam


class AntennaMixer(Mixer):
    """
    Implements a mixing matrix for an antenna array, incorporating the effects of
    direction of arrival (DOA) and individual antenna element gains.
    
    By default, the array is modeled as a Uniform Linear Array (ULA) with omnidirectional
    elements. Placeholders are provided for custom, individual element patterns and non-uniform
    element positions to allow easy extension to more complex antenna geometries.
    
    Van Trees Vector Notation is used to build the array steering/manifold vectors.
    """

    def __init__(
        self,
        num_elements: int,
        element_spacing_ratio: float = 0.5,
        element_positions: np.ndarray | None = None,
    ):
        """
        Initializes the AntennaMixer with the specified array configuration.

        Parameters:
            num_elements (int): The number of antenna elements in the array (M).
            element_spacing_ratio (float): The ratio of element spacing (d) to wavelength (lambda), 
                                           i.e., d/lambda. Defaults to 0.5 (half-wavelength spacing).
            element_positions (np.ndarray, optional): A 1D array of length M representing the individual
                                                      element positions normalized by wavelength.
                                                      If None, defaults to a standard ULA with uniform spacing.
        """
        super().__init__()
        self.M = num_elements
        self.element_spacing_ratio = element_spacing_ratio
        self.signal_doas = {}
        self.beamform_weights = np.ones((self.M, 1))
        # PLACEHOLDER: Individual Element Positions
        # If element_positions is provided, we use those custom positions (e.g. non-uniform linear array).
        # For multi-dimensional arrays (2D/3D), this could be extended to coordinate vectors.
        if element_positions is not None:
            if len(element_positions) != num_elements:
                raise ValueError(
                    f"Length of element_positions ({len(element_positions)}) must match num_elements ({num_elements})."
                )
            self.element_positions = np.asarray(element_positions, dtype=float)
        else:
            # Default to a standard Uniform Linear Array (ULA)
            self.element_positions = np.arange(num_elements) * self.element_spacing_ratio

    def get_element_gain(self, element_idx: int, angle: float) -> complex:
        """
        Computes the complex gain of an individual antenna element at a specific arrival angle.

        PLACEHOLDER: Individual Element Patterns
        Currently, elements are modeled as omnidirectional with unity complex gain (1.0).
        This method can be overridden or modified to incorporate individual gains/phases and 
        non-uniform radiation patterns (e.g., dipoles, patch patterns, directional gains) as a 
        function of angle.

        Parameters:
            element_idx (int): The 0-based index of the antenna element (0 to M-1).
            angle (float): Direction of Arrival (DOA) angle in radians (relative to broadside, where 0 is perpendicular to array).

        Returns:
            complex: Complex gain contribution of the element.
        """
        if not (0 <= element_idx < self.M):
            raise IndexError(f"element_idx {element_idx} is out of bounds for array size {self.M}.")
        
        # Omnidirectional element pattern placeholder (unity gain)
        return 1.0 + 0.0j

    def compute_manifold_vector(self, angle: float) -> np.ndarray:
        """
        Computes the steering (manifold) vector for the antenna array for a given angle.
        
        According to Van Trees vector notation, the steering vector incorporates the spatial phase
        delay/advance of the wave across the array relative to the reference coordinate origin,
        multiplied by the individual element gain patterns.

        For a 1D array along the axis, the spatial phase delay at element m is:
            psi_m = 2 * pi * (x_m / lambda) * sin(theta)
        And the response is:
            v_m = g_m(theta) * exp(j * psi_m)

        Parameters:
            angle (float): Direction of Arrival (DOA) angle in radians (relative to broadside).

        Returns:
            np.ndarray: A complex array of shape (M, 1) representing the steering vector.
        """
        # Phase delay contribution at each element based on its position
        # element_positions is already normalized by wavelength (x_m / lambda)
        spatial_phases = 2 * np.pi * self.element_positions * np.sin(angle)
        
        # Initialize steering vector
        steering_vector = np.zeros(self.M, dtype=np.complex128)
        
        for m in range(self.M):
            gain = self.get_element_gain(m, angle)
            steering_vector[m] = gain * np.exp(1j * spatial_phases[m])
            
        return steering_vector.reshape((self.M, 1))

    def antenna_mixing_matrix(self, angles: Union[List[float], np.ndarray]) -> np.ndarray:
        """
        Computes the MxN mixing matrix H, where each column is the steering (manifold) vector
        corresponding to the Direction of Arrival (DOA) of each source signal.

        Parameters:
            angles (list of float or np.ndarray): Directions of Arrival (DOAs) in radians for each of the N signals.

        Returns:
            np.ndarray: The mixing matrix H of shape (M, N).
        """
        angles_arr = np.asarray(angles, dtype=float)
        N = len(angles_arr)
        
        # Construct H of shape (M, N) column-by-column
        A = np.zeros((self.M, N), dtype=np.complex128)
        for n in range(N):
            A[:, n] = self.compute_manifold_vector(angles_arr[n]).flatten()
            self.signal_doas[n] = angles[n]

        self.set_mixing_matrix(A)
        return A


    def compute_scanned_response(
        self, X: np.ndarray = None, angle_resolution: int = 722
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Computes the spatial power response (spectrum) by scanning a conventional delay-and-sum
        beamformer across the angles from -pi/2 to pi/2 (-90 to +90 degrees).

        This is done by calculating the received signal sample covariance matrix:
            R = (1 / L) * X * X^H
        And for each scan angle phi, computing the beamformer output power:
            P(phi) = w(phi)^H * R * w(phi)
        where w(phi) = (1 / M) * v(phi) is the conventional beamformer weight vector.

        Parameters:
            X (np.ndarray): The received element channel data matrix of shape (M, L).
            angle_resolution (int): The number of angular steps to compute across [-pi/2, pi/2].
                                     Defaults to 361 (yielding 0.5 degree steps).

        Returns:
            Tuple[np.ndarray, np.ndarray]:
                - scan_angles (np.ndarray): 1D array of scan angles in radians, length `angle_resolution`.
                - powers_db (np.ndarray): 1D array of power response values in decibels, length `angle_resolution`.
        """
        if X is None:
            X = self.Y

        M_elements, L_samples = X.shape
        if M_elements != self.M:
            raise ValueError(
                f"Input data X has {M_elements} elements, but AntennaMixer is initialized with {self.M}."
            )

        # Compute sample covariance matrix R (M x M)
        R = (1.0 / L_samples) * np.matmul(X, X.conj().T)

        # Scan angles from -pi/2 to pi/2 (radians)
        scan_angles = np.linspace(-np.pi / 2, np.pi / 2, angle_resolution)
        scans = np.zeros(angle_resolution)
        beam_scans = np.zeros(angle_resolution)

        # Conventional (Bartlett) Beamforming power spectrum calculation
        for idx, phi in enumerate(scan_angles):
            v = self.compute_manifold_vector(phi)  # (M, 1) steering vector
            w =  v                 # (M, 1) normalized weight vector
            
            # P(phi) = w^H * R * w
            scan = np.abs(np.matmul(w.conj().T, np.matmul(R, w)))[0, 0]
            scans[idx] = max(scan, 1e-15)  # Avoid absolute zero power

            beam_scan = np.abs(self.beamform_weights.conj().T @ v)[0]
            beam_scans[idx] = max(beam_scan, 1e-15)  # Avoid absolute zero power

        # Convert to Decibels (dB)
        scan_db = 10 * np.log10(scans)
        beam_scan_db = 20*np.log10(beam_scans)
        return scan_angles, scan_db, beam_scan_db


    def fixed_beamform(self, weights: np.ndarray):
        out = np.matmul(weights.conj().T, self.Y)
        N, L = self.Y.shape
        self.B = out

    def steering_matrix(self, angle: float):
        return self.compute_manifold_vector(angle)

    def beamform(self, style:str = "classic", weighting:str = None, weights:np.ndarray = None, steering_doa:float = 0.0):
        window = np.ones((self.M, 1))
        match weighting:
            case "Bartlett":
                window = np.bartlett(self.M)
            case "Hamming":
                window = np.hamming(self.M)
            case "Hann":
                window = np.hanning(self.M)
            case "taylor":
                window = taylor(self.M)
            case _:
                print("Using default rectangular window...")

        match style:
            case "classic":
                w = self.compute_manifold_vector(np.radians(steering_doa)) / self.M
                w = w
                self.fixed_beamform(w)
            case "custom":
                w = weights
                w = w
                self.fixed_beamform(w)
            case "adaptive":
                v = self.compute_manifold_vector(np.radians(steering_doa))
                self.B, w = beam.frost(X=self.Y, C=v, f=np.ones((1,1)), mu=0.9, method="iterative")

            case _:
                raise ValueError("Invalid beamforming style specified.")

        self.beamform_weights = w # save for later



if __name__ == "__main__":
    # Self-test block to demonstrate functionality and verify implementation
    from classes_test.SignalGenerator import SignalGenerator, SignalConfig

    print("--- AntennaMixer Scanned Response & Tabbed Visualization Verification ---")

    # Define array parameters
    M = 8  # 8 elements for high beamforming resolution
    spacing_ratio = 0.5  # d/lambda = 0.5 (half-wavelength spacing)
    
    mixer = AntennaMixer(num_elements=M, element_spacing_ratio=spacing_ratio)
    
    # Generate 3 signals (N = 3) of length L = 1000
    Fs = 10e3
    N_samples = 1000
    
    sig_gen = SignalGenerator()
    
    # Signal 1: CW at 100 Hz
    config1 = SignalConfig(sample_rate=Fs, center_frequency=100.0, amplitude=1.0, min_num_samples=N_samples, phase_offset=0.0)
    sig1 = sig_gen.generate_CW(config=config1)
    
    # Signal 2: LFM sweeping from -500 Hz to 500 Hz
    config2 = SignalConfig(sample_rate=Fs, lfm_f_lower=-500.0, lfm_f_upper=500.0, amplitude=1.5, min_num_samples=N_samples, phase_offset=0.5)
    sig2 = sig_gen.generate_LFM(config=config2)
    
    # Signal 3: Bandlimited Noise in [-200, 200] Hz
    config3 = SignalConfig(sample_rate=Fs, noise_f_lower=-200.0, noise_f_upper=200.0, amplitude=30, min_num_samples=N_samples)
    sig3 = sig_gen.generate_Noise(config=config3)
    
    signals = [sig1, sig2, sig3]
    
    # Directions of arrival in radians for the 3 signals: -30 degrees, 10 degrees, 45 degrees
    angles = np.radians([-30, 10, 32])
    
    print(f"Number of Antenna Elements (M): {M}")
    print(f"Number of Incoming Signals (N): {len(signals)}")
    print(f"DOA Angles (degrees): {[-30, 10, 32]}")
    
    # 1. Mix the signals to generate the channel matrix X (M x L)
    M = mixer.antenna_mixing_matrix(angles)
    print(f"Mixing matrix: ")
    A = mixer.get_mixing_matrix()
    for row in A:
        for val in row:
            print(f"{val:.2f} | ", end=" ")
        print("")
    mixer.mix_signals(signals)
    X = mixer.Y
    print(f"Mixed Output Matrix X Shape: {X.shape}")
    print(f"Mixing matrix: ")
    for row in M:
        for val in row:
            print(f"{val:.2f} | ", end=" ")
        print("")
    
    # 2. Compute Inverse and Condition Number
    cond_num = mixer.calculate_condition_number()
    print(f"Condition Number of H: {cond_num:.4f}")

    
    print("\nVerification Complete.")
