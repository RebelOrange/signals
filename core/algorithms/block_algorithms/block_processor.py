import numpy as np
from fontTools.config import Config

from .providers.interfaces import IBlockProcessingProvider
from typing import Any, List
from .providers.registry import _PROVIDER_REGISTRY

class BlockProcessor:
    def __init__(self, provider: IBlockProcessingProvider) -> None:
        self._provider = provider

    @classmethod
    def from_config(cls, config: Any) -> 'BlockProcessor':
        provider_class = _PROVIDER_REGISTRY.get(type(config))
        if not provider_class:
            raise ValueError("Invalid config")

        provider_inst = provider_class(config)
        return cls(provider_inst)