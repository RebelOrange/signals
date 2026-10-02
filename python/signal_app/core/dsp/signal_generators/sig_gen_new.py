import numpy as np

from ..datatypes import TimeGrid, PulsedSignalConfig, SignalEvent
from .signal_providers.interfaces import ISignalProvider
from typing import Any, List
from .signal_providers.registry import _PROVIDER_REGISTRY
from ..signal_new import Signal

class SignalGenerator:
    def __init__(self, time_grid: TimeGrid,provider: ISignalProvider = None):
        self._provider: ISignalProvider = provider
        self._time_grid: TimeGrid = time_grid
        print(f"SigGen: time_grid: {self._time_grid}"
              f" | total samples: {self.total_samples}")

    @property
    def total_samples(self) -> int:
        return int(np.ceil(self._time_grid.duration*self.sample_rate))

    @property
    def sample_rate(self) -> float:
        return self._time_grid.sample_rate

    def set_config(self, config: Any):
        self._provider = self.get_provider(config)

    @classmethod
    def from_config(cls, time_grid: TimeGrid, signal_config: Any):
        """Factory method dependency injection, derives provider from config"""
        provider_class = _PROVIDER_REGISTRY.get(type(signal_config))

        if not provider_class:
            raise ValueError(f"No provider registered for {type(signal_config)}")

        provider_inst = provider_class(signal_config)
        return cls(provider_inst, time_grid)

    def get_provider(self, config: Any) -> ISignalProvider:
        provider_class = _PROVIDER_REGISTRY.get(type(config))
        if not provider_class:
            raise ValueError(f"No provider registered for {type(config)}")
        provider_inst = provider_class(config)
        return provider_inst

    def create_empty_timeseries(self) -> np.ndarray:
        total_samples = int(np.ceil(self._time_grid.duration*self._time_grid.sample_rate))
        return np.zeros(total_samples, dtype=np.complex128)

    def generate_iq(self) -> np.ndarray:
        t = np.arange(0, self._time_grid.duration, 1/self._time_grid.sample_rate)
        return self._provider.generate_iq(t)

    def generate_signal(self, config: Any = None) -> Signal:
        if config is not None:
            self._provider = self.get_provider(config)
        iq = self.generate_iq()
        event = SignalEvent(start_time=0,
                            duration=self._time_grid.duration,
                            start_idx=0,
                            end_idx=len(iq),
                            waveform_config=config,
                            pulse_iq=iq)
        return Signal(iq=iq, events=[event], sample_rate=self.sample_rate)

    def create_pulsed_signal(self, pulsed_configs: List[PulsedSignalConfig], label:str="Unlabeled") -> Signal:
        all_iq = np.zeros(self.total_samples, dtype=np.complex128)
        print(f"total samples: {self.total_samples}")
        events = [] # pulse events

        for p_cfg in pulsed_configs:
            gate = p_cfg.gate
            print(f"Start time: {gate.start_time:0.6f}, Fs: {self.sample_rate:0.6f}")
            start_idx = int(round(gate.start_time*self.sample_rate))
            num_samps = int(round(gate.duration*self.sample_rate))
            end_idx = start_idx + num_samps

            # pulse time:
            t = np.arange(num_samps, dtype=np.float64)/self.sample_rate
            print(f"Duration {gate.duration:0.6f}, num_samps {num_samps}, start_idx {start_idx}, end_idx {end_idx}")
            print(f"Time len = {len(t):0.6f}")
            provider = self.get_provider(p_cfg.waveform_config)
            pulse_iq = provider.generate_iq(t)

            all_iq[start_idx:end_idx] += pulse_iq
            event = SignalEvent(start_time=gate.start_time,
                                duration=gate.duration,
                                start_idx=start_idx,
                                end_idx=end_idx,
                                label=label,
                                waveform_config=p_cfg.waveform_config,
                                pulse_iq=pulse_iq)

            events.append(event)

        # generate final signal
        sig = Signal(iq=all_iq, events=events, sample_rate=self.sample_rate, label=label)
        return sig






if __name__ == "__main__":
    from signal_providers.CW import CwConfig
    from signal_providers.FM import LFMConfig
    from signal_providers.PSK import BPSKConfig, CodeConstructer
    from signal_providers.Noise import NoiseConfig
    from dsp.datatypes import PulsedSignalConfig, TimeGrid, TimeGate
    from dsp.signal_new import Signal
    from mpl.dsp.signal_plotter import plot_iq_timeseries, plot_fft
    import matplotlib.pyplot as plt

    #config = CwConfig(frequency=100, phase=np.pi/2, amplitude=1)
    #config = LFMConfig(chirp_bandwidth=500, frequency_center=0, pulse_width=50e-3)
    code_config = BPSKConfig(frequency=0, code=CodeConstructer.barker(13), phase=30*np.pi/180)
    pulse1 = PulsedSignalConfig(gate=TimeGate(start_time=500e-6, stop_time=1000e-6), waveform_config=code_config)
    noise_config = NoiseConfig(bandwidth=2e6, frequency_center=0e-3, variance=4.0)
    pulse2 = PulsedSignalConfig(gate=TimeGate(start_time=1500e-6, stop_time=2000e-6), waveform_config=noise_config)


    t = np.arange(0, 1000)
    t = TimeGrid(sample_rate=4e3, duration=50e-3)
    #sigGen = SignalGenerator.from_config(signal_config=config, time_grid=t)
    #sig = sigGen.generate_signal()
    sigGen = SignalGenerator(time_grid=TimeGrid(sample_rate=4e6, duration=2500e-6))
    sig = sigGen.create_pulsed_signal([pulse1, pulse2])

    fig, ax = plt.subplots()
    plot_iq_timeseries(iq=sig.events[0].pulse_iq, t=np.arange(len(sig.events[0].pulse_iq)),ax=ax)
    print(sig.iq.shape)

    plt.show()