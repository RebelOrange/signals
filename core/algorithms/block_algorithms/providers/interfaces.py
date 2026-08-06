import numpy as np
from typing import Protocol

class IBlockProcessingProvider(Protocol):
    def process_datamatrix(self, X: np.ndarray) -> np.ndarray:
        ...