import numpy as np
from typing import Protocol

class ISignalProvider(Protocol):
    def generate_iq(self, time_vector: np.ndarray) -> np.ndarray:
        ...