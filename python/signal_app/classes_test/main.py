from classes_test.ComplexSignal import *
from classes_test.AntennaMixer import *
from classes_test.SignalGenerator import *

print("--- AntennaMixer Scanned Response Verification ---")

## Define array parameters
M = 8
spacing_ratio = 0.5  # d/lambda = 0.5 (half-wavelength spacing)

mixer = AntennaMixer(num_elements=M, element_spacing_ratio=spacing_ratio)

## Signals
Fs = 10e3
N_samples = 1000

sig_gen = SignalGenerator()

# Signal 1: CW at 100 Hz
config1 = SignalConfig(sample_rate=Fs, center_frequency=100.0, amplitude=1.0, min_num_samples=N_samples,
                       phase_offset=0.0)
sig1 = sig_gen.generate_CW(config=config1)

# Signal 2: LFM sweeping from -500 Hz to 500 Hz
config2 = SignalConfig(sample_rate=Fs, lfm_f_lower=-500.0, lfm_f_upper=500.0, amplitude=1.5, min_num_samples=N_samples,
                       phase_offset=0.5)

# Signal 3: Bandlimited Noise in [-200, 200] Hz
config3 = SignalConfig(sample_rate=Fs, noise_f_lower=-200.0, noise_f_upper=200.0, amplitude=0.5,
                       min_num_samples=N_samples)
sig2 = sig_gen.generate_Noise(config=config3)

signals = [sig1, sig2]

## DOAs
angles_d = [0, 40]
angles = np.radians(angles_d)

print(f"Number of Antenna Elements (M): {M}")
print(f"Number of Incoming Signals (N): {len(signals)}")
print(f"DOA Angles (degrees): {angles_d}")

X = mixer.mix_signals(signals, angles)
print(f"Mixed Output Matrix X Shape: {X.shape}")

inv_H, cond_num = mixer.compute_inverse_and_condition_number(angles)
print(f"Condition Number of H: {cond_num:.4f}")

mixer.plot_scanned_response(X, true_angles=angles, angle_unit="degrees")
