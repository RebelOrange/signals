import numpy as np
from classes_test.AntennaMixer import AntennaMixer
from classes_test.SignalGenerator import SignalGenerator, SignalConfig
from classes_test.Beamformer import Beamformer


def main():
    # 1. Initialize AntennaMixer
    num_elements = 20
    a = AntennaMixer(num_elements=num_elements)

    # 2. Generate signals (same as AntennaPlotter.py)
    siggen = SignalGenerator()
    config1 = SignalConfig(sample_rate=10e3,
                           center_frequency=0,
                           SNR=-3,
                           lfm_f_lower=-3000,
                           lfm_f_upper=3000,
                           noise_f_lower=-1000,
                           noise_f_upper=2000,
                           amplitude=0.000,
                           min_num_samples=1000,
                           phase_offset=0)
    config2 = SignalConfig(sample_rate=10e3,
                           center_frequency=0,
                           SNR=-3,
                           lfm_f_lower=-3000,
                           lfm_f_upper=3000,
                           noise_f_lower=-4500,
                           noise_f_upper=4500,
                           amplitude=1,
                           min_num_samples=1000,
                           phase_offset=0)
    config3 = SignalConfig(sample_rate=10e3,
                           center_frequency=0,
                           SNR=-3,
                           lfm_f_lower=-3000,
                           lfm_f_upper=3000,
                           noise_f_lower=-300,
                           noise_f_upper=300,
                           amplitude=0.01,
                           min_num_samples=1000,
                           phase_offset=0)

    s0 = siggen.generate_Noise(config=config1)
    s1 = siggen.generate_Noise(config=config2)  # Strong interferer at 10 degrees
    s2 = siggen.generate_LFM(config=config3)  # Weak desired signal at 25 degrees

    signals = [s0, s1, s2]
    angles = np.radians([-10, 10, 25])

    a.antenna_mixing_matrix(angles=angles)
    mixed_signals = a.mix_signals(signals)

    # 3. Perform original adaptive beamforming (steering at 25)
    print("--- Original MVDR ---")
    a.beamform(style="adaptive", weighting=None, steering_doa=25)
    w_orig = a.beamform_weights  # already scaled by 1/M in original code

    # 4. Let's analyze the spatial response
    # Steering DOA is 25 degrees. Let's check response at 25 degrees and 10 degrees (interferer)
    v_look = a.compute_manifold_vector(np.radians(25))
    v_interf = a.compute_manifold_vector(np.radians(10))

    # beamform_weights has 1/M factor applied. Let's undo it or use it as is:
    # Actually, let's see how much they gain in dB
    # Gain in dB is 20 * log10(abs(w^H * v))
    gain_look_orig = np.abs(w_orig.conj().T @ v_look)[0]
    gain_interf_orig = np.abs(w_orig.conj().T @ v_interf)[0]

    print(f"Original weights scaled by 1/M:")
    print(f"Gain at 25 deg (look): {20 * np.log10(gain_look_orig):.2f} dB (amplitude: {gain_look_orig:.4f})")
    print(f"Gain at 10 deg (interferer): {20 * np.log10(gain_interf_orig):.2f} dB (amplitude: {gain_interf_orig:.4f})")

    # Let's also print unscaled original gain (multiplying by M)
    gain_look_orig_unscaled = gain_look_orig * num_elements
    gain_interf_orig_unscaled = gain_interf_orig * num_elements
    print(f"Original weights unscaled (no 1/M):")
    print(
        f"Gain at 25 deg (look): {20 * np.log10(gain_look_orig_unscaled):.2f} dB (amplitude: {gain_look_orig_unscaled:.4f})")
    print(
        f"Gain at 10 deg (interferer): {20 * np.log10(gain_interf_orig_unscaled):.2f} dB (amplitude: {gain_interf_orig_unscaled:.4f})")

    # 5. Let's run a clean MVDR (without the zero C_null constraint)
    print("\n--- Clean MVDR (No C_null) ---")
    # Let's compute manually:
    # w_mvdr = S_inv @ v_look / (v_look^H @ S_inv @ v_look)
    X_data = a.Y
    S = X_data @ X_data.conj().T
    S_inv = np.linalg.pinv(S)

    w_mvdr = S_inv @ v_look / (v_look.conj().T @ S_inv @ v_look)

    # Gain is w_mvdr^H @ v
    gain_look_clean = np.abs(w_mvdr.conj().T @ v_look)[0, 0]
    gain_interf_clean = np.abs(w_mvdr.conj().T @ v_interf)[0, 0]

    print(f"Gain at 25 deg (look): {20 * np.log10(gain_look_clean):.2f} dB (amplitude: {gain_look_clean:.4f})")
    print(
        f"Gain at 10 deg (interferer): {20 * np.log10(gain_interf_clean):.2f} dB (amplitude: {gain_interf_clean:.4f})")


if __name__ == "__main__":
    main()
