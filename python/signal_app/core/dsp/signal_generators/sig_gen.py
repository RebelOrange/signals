
import numpy as np
from typing import TypedDict
from core.dsp.iq_signal import Signal


class SignalConfig(TypedDict, total=False):
    sample_rate: float
    center_frequency: float
    amplitude: float
    min_num_samples: int
    phase_offset: float
    SNR: float
    JSR: float
    # LFM
    lfm_f_lower: float
    lfm_f_upper: float
    # Noise
    noise_var: float
    noise_BW: float
    noise_f_lower: float
    noise_f_upper: float
    # BPSK
    bpsk_code: list[float]
    # time masking
    mask_type: str
    start_time: float
    stop_time: float
    start_sample: int
    stop_sample: int
    total_time: float
    total_samples: int


class SignalGenerator:
    def __init__(self):
        pass

    @staticmethod
    def get_config_mask(config: SignalConfig) -> tuple[np.ndarray, int]:
        mask_type = config.get("mask_type", None)
        if mask_type is None:
            return None, None
        if mask_type == "time":
            fs = config["sample_rate"]
            start_time = config.get("start_time", 0)
            stop_time = config.get("stop_time", 0)
            total_time = config.get("total_time", 0)
            start_sample = np.int32(np.floor(start_time * fs))
            stop_sample = np.int32(np.floor(stop_time * fs))
            total_samples = np.int32(np.floor(total_time * fs))
        else:
            # sample based mask
            print("made it")
            start_sample = config.get("start_sample")
            stop_sample = config.get("stop_sample")
            total_samples = config.get("total_samples")
        mask = np.zeros(total_samples)
        mask[start_sample:stop_sample] = 1


        return mask, start_sample


    @staticmethod
    def generate_CW(config: SignalConfig | None = None) -> Signal:
        f_0 = config["center_frequency"]
        amp = config["amplitude"]
        Fs = config["sample_rate"]
        Ts = 1. / Fs
        N = config["min_num_samples"]
        phase_offset = config["phase_offset"]
        # local duration and N samples
        duration = N * Ts

        t = np.arange(0.0, duration, Ts)
        x = amp * np.exp(1j * (2 * np.pi * f_0 * t + phase_offset))  # IQ

        mask, start_samp = SignalGenerator.get_config_mask(config=config)
        if mask is not None:
            zeros = np.zeros_like(mask, dtype=np.complex128)
            sig = zeros
            sig[start_samp:(start_samp + N)] = x
            x = sig


        # create signal class and add features to it
        signal = Signal(iq=x,
                        fs=config["sample_rate"],
                        label="CW")
        return signal

    @staticmethod
    def generate_system_noise(config: SignalConfig | None = None) -> Signal:
        mask, start_samp = SignalGenerator.get_config_mask(config=config)
        if mask is not None:
            N = len(mask)
        else:
            N = config["min_num_samples"]
        noise = np.zeros(N, dtype=np.complex128)

        print(f"Noise len {N}")
        if config.get("SNR", None) is not None:
            amp = config["amplitude"]
            snr = 10 ** (config["SNR"] / 10)
            noise_amp = np.sqrt(amp / snr)
            noise = noise_amp * np.random.normal(0, 1, N) + 1j * noise_amp * np.random.normal(0, 1, N)
            print(f"noise_amp {noise_amp}")
        duration = N * (1. / config["sample_rate"])
        t = np.arange(0.0, duration, 1. / config["sample_rate"])

        signal = Signal(iq=noise,
                        fs=config["sample_rate"],
                        label="system_noise")


        return signal

    @staticmethod
    def generate_LFM(config: SignalConfig | None = None) -> Signal:
        f_lower = config["lfm_f_lower"]
        f_upper = config["lfm_f_upper"]
        amp = config["amplitude"]
        Fs = config["sample_rate"]
        Ts = 1. / Fs
        N = config["min_num_samples"]
        phase_offset = config.get("phase_offset",0.0)
        duration = N * Ts

        t = np.arange(0.0, duration, Ts)
        k = (f_upper - f_lower) / duration  # sweep rate
        phase = 2 * np.pi * (f_lower * t + 0.5 * k * (t ** 2)) + phase_offset
        x = amp * np.exp(1j * phase)

        mask, start_samp = SignalGenerator.get_config_mask(config=config)
        if mask is not None:
            zeros = np.zeros_like(mask, dtype=np.complex128)
            sig = zeros
            sig[start_samp:(start_samp+N)] = x
            x = sig

        # create signal class and add features to it
        signal = Signal(iq=x,
                        fs=config["sample_rate"],
                        label="LFM")
        return signal

    @staticmethod
    def generate_Noise(config: SignalConfig | None = None) -> Signal:
        config = config or {}
        Fs = config.get("sample_rate", 10e3)
        Ts = 1. / Fs
        N = config.get("min_num_samples", 1000)

        f_lower = config.get("noise_f_lower", -Fs / 2)
        f_upper = config.get("noise_f_upper", Fs / 2)
        amp = config.get("amplitude", 1.0)

        duration = N * Ts
        t = np.arange(0.0, duration, Ts)

        # 1. Choose N_fft (at least 4x larger to prevent temporal aliasing and ensure fine frequency bins)
        N_fft = int(2 ** (int(np.ceil(np.log2(N))) + 2))

        # 2. Get frequency bins
        freqs = np.fft.fftfreq(N_fft, d=Ts)

        # 3. Create a mask for frequencies within [f_lower, f_upper]
        band_mask = (freqs >= f_lower) & (freqs <= f_upper)
        num_active_bins = np.sum(band_mask)

        # Handle edge case where requested band contains no bins
        if num_active_bins == 0:
            closest_bin = np.argmin(np.abs(freqs - (f_lower + f_upper) / 2))
            band_mask[closest_bin] = True
            num_active_bins = 1

        # 4. Generate frequency-domain complex white noise (flat spectrum)
        spectrum = np.zeros(N_fft, dtype=np.complex128)
        phases = np.random.uniform(0, 2 * np.pi, size=num_active_bins)
        spectrum[band_mask] = np.exp(1j * phases)

        # 5. Transform to time domain
        x_full = np.fft.ifft(spectrum)

        x = amp*x_full[:N]

        # Scale to variance to desired noise power
        des_var = config.get("noise_var", 1) # linear
        var = np.dot(x, x.conj())/len(x)
        scale_factor = des_var / var
        x *= np.sqrt(scale_factor)

        mask, start_samp = SignalGenerator.get_config_mask(config=config)
        if mask is not None:
            zeros = np.zeros_like(mask, dtype=np.complex128)
            sig = zeros
            sig[start_samp:(start_samp + N)] = x
            x = sig

        signal = Signal(iq=x,
                        fs=config["sample_rate"],
                        label="Noise")
        return signal

    @staticmethod
    def generate_BPSK(config: SignalConfig | None = None) -> Signal:
        config = config or {}

        Fs = config.get("sample_rate", 10e3)
        Ts = 1. / Fs
        f_0 = config.get("center_frequency", 0.0)
        amp = config.get("amplitude", 1.0)
        phase_offset = config.get("phase_offset", 0.0)

        code = np.asarray(config.get("bpsk_code", [1.0, -1.0]), dtype=float)

        if len(code) == 0:
            raise ValueError("bpsk_code must contain at least one chip.")

        chip_width = config.get("bpsk_chip_width", None)

        if chip_width is not None:
            samples_per_chip = int(round(chip_width * Fs))

            if samples_per_chip < 1:
                raise ValueError("bpsk_chip_width is too small for the configured sample_rate.")

            N = len(code) * samples_per_chip
            min_num_samples = N
        else:
            min_num_samples = config.get("min_num_samples", 1000)
            samples_per_chip = int(np.ceil(min_num_samples / len(code)))
            N = len(code) * samples_per_chip


        baseband_code = np.repeat(code, samples_per_chip)

        duration = N * Ts
        t = np.arange(0.0, duration, Ts)

        if len(t) > N:
            t = t[:N]
        elif len(t) < N:
            t = np.arange(N) * Ts

        carrier = np.exp(1j * (2 * np.pi * f_0 * t + phase_offset))
        x = amp * baseband_code * carrier
        trunc_x = x[:min_num_samples]

        mask, start_samp = SignalGenerator.get_config_mask(config=config)
        if mask is not None:
            zeros = np.zeros_like(mask, dtype=np.complex128)
            sig = zeros
            sig[start_samp:(start_samp + N-1)] = trunc_x
            trunc_x = sig

        signal = Signal(iq=trunc_x,
                        fs=config["sample_rate"],
                        label="BPSK")
        return signal

    @staticmethod
    def barker_code(order: int) -> list[int]:
        match order:
            case 13:
                return [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, -1, 1, 1]
        return []



if __name__ == "__main__":
    config = SignalConfig(sample_rate=10e3, center_frequency=0, lfm_f_lower=-3000, lfm_f_upper=3000, noise_f_lower=-30,
                          noise_f_upper=30, amplitude=1, min_num_samples=1000, phase_offset=0)
    print(config)
    sigGen = SignalGenerator()
    signal = sigGen.generate_Noise(config=config)

    barker_13 = [
        1, 1, 1, 1, 1,
        -1, -1,
        1, 1,
        -1,
        1,
        -1,
        1,
    ]

    config = SignalConfig(
        sample_rate=10e3,
        center_frequency=10,
        amplitude=1,
        min_num_samples=1000,
        phase_offset=0,
        bpsk_code=barker_13,
    )

    print(config)

    sigGen = SignalGenerator()
    signal = sigGen.generate_BPSK(config=config)

    print(f"Signal type: {signal.signal_type}")
    print(f"Signal length: {signal.length}")
    print(f"Sample rate: {signal.sample_rate}")
    print(f"Samples per chip: {signal.length // len(barker_13)}")

