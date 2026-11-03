from abc import abstractmethod, ABC
from typing import Any
from core.dsp.algorithms.canceller_algorithms.providers.registry import register_provider, _PROVIDER_REGISTRY
from core.dsp.algorithms.canceller_algorithms.providers.registry import IFilterProvider
import numpy as np


# a factory class that calls from the
# provider folder with specific implementations

# STAP Sidelobe Cancellation Processor
class CancellerProcessor(ABC):
    def __init__(self, provider: IFilterProvider = None):
        self.config: IFilterProvider = None
        self._provider = self.get_provider(config)

    @classmethod
    def from_config(cls, config: IFilterProvider):
        provider_class = _PROVIDER_REGISTRY.get(type(config))
        if not provider_class:
            raise NotImplementedError
        provider_inst = provider_class(config)
        return cls(provider_inst)

    def set_config(self, config: IFilterProvider):
        self._provider = self.get_provider(config)

    def run(self, X: np.array, d: np.array, precision:str="float"):
        return self._provider.run(X=X, d=d, precision=precision)

    def get_provider(self, config: Any) -> IFilterProvider:
        provider_class = _PROVIDER_REGISTRY.get(type(config))
        if not provider_class:
            raise NotImplementedError
        provider_inst = provider_class(config)
        return provider_inst


if __name__ == "__main__":
    from core.dsp.algorithms.canceller_algorithms.providers.LMS import LmsConfig
    import matplotlib.pyplot as plt
    from core.vitis.pyap_fixed import *

    config = LmsConfig()
    proc = CancellerProcessor.from_config(config)
    print(proc._provider)

    # random data
    N = 8096
    x = (100.0*(np.random.normal(size=N)+1j*np.random.normal(size=N)))[np.newaxis,:]
    x_shift = 3*np.exp(1j*0.75*np.pi)*x
    x_shift_2 = 6 * np.exp(1j * -0.75 * np.pi) * x

    X = np.vstack((x_shift))
    R = X@X.conj().T
    np.linalg.matrix_rank(R)
    print(f"R:")
    print(R)
    print(f"rank: {np.linalg.matrix_rank(R)}")
    print(np.shape(x))
    print(np.shape(X))

    e, y, W = proc.run(X=X, d=x[0,:], precision="ap_fixed")

    plt.figure()
    plt.plot(np.real(e))
    plt.plot(np.imag(e))

    plt.figure()
    plt.plot(np.real(W[0,:]),"b-")
    plt.plot(np.imag(W[0,:]),"r-")
    plt.plot(np.real(W[1,:]),"b--")
    plt.plot(np.imag(W[1,:]),"r--")

    print(np.mean(np.real(W[0,200:])))




    plt.show()

    pass

