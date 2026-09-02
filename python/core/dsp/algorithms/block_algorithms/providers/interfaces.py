import numpy as np
from typing import Protocol

class IBlockProcessingProvider(Protocol):
    def process_datamatrix(self, X: np.ndarray) -> np.ndarray:
        ...

    def calculate_weights(self, X: np.ndarray, steering_constraint, amp_constraint) -> np.ndarray:
        ...