from typing import Type, Dict, Any, Tuple
import numpy as np
from typing import Protocol

_PROVIDER_REGISTRY: Dict[Type, Type] = {}

def register_provider(config_class: Type):
    """automatically links a config TYPE to a provider"""
    def wrapper(provider_class: Type):
        _PROVIDER_REGISTRY[config_class] = provider_class
        return provider_class
    return wrapper

class IFilterProvider(Protocol):
    def run(self, X:np.ndarray, d:np.ndarray, precision:str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        ...
