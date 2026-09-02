from typing import Type, Dict, Any

_PROVIDER_REGISTRY: Dict[Type, Type] = {}

def register_provider(config_class: Type):
    """automatically links a config TYPE to a provider"""
    def wrapper(provider_class: Type):
        _PROVIDER_REGISTRY[config_class] = provider_class
        return provider_class
    return wrapper