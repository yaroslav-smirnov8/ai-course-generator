"""
Adapter factory and initialization.

This module provides a factory function to create the appropriate adapter
based on configuration.
"""

import os
from typing import Dict, Any, Optional
from .base import BaseAIAdapter
from .mock import MockAdapter
from .custom import CustomAdapter


# Registry of available adapters
ADAPTER_REGISTRY: Dict[str, type] = {
    "mock": MockAdapter,
    "custom": CustomAdapter,
}


def create_adapter(
    adapter_type: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> BaseAIAdapter:
    """
    Factory function to create an AI adapter instance.
    
    Args:
        adapter_type: Type of adapter to create (mock, custom, etc.)
                     If None, reads from AI_ADAPTER environment variable
        config: Optional configuration dictionary for the adapter
        
    Returns:
        Initialized adapter instance
        
    Raises:
        ValueError: If adapter_type is not recognized
        
    Example:
        >>> adapter = create_adapter("mock")
        >>> adapter = create_adapter("custom", {"api_key": "sk-..."})
    """
    if adapter_type is None:
        adapter_type = os.getenv("AI_ADAPTER", "mock").lower()
    
    adapter_type = adapter_type.lower()
    
    if adapter_type not in ADAPTER_REGISTRY:
        available = ", ".join(ADAPTER_REGISTRY.keys())
        raise ValueError(
            f"Unknown adapter type: {adapter_type}. "
            f"Available adapters: {available}"
        )
    
    adapter_class = ADAPTER_REGISTRY[adapter_type]
    return adapter_class(config)


def register_adapter(name: str, adapter_class: type) -> None:
    """
    Register a custom adapter class.
    
    This allows you to add your own adapter implementations at runtime.
    
    Args:
        name: Name to register the adapter under
        adapter_class: Adapter class (must inherit from BaseAIAdapter)
        
    Example:
        >>> from my_adapters import MyCustomAdapter
        >>> register_adapter("my_adapter", MyCustomAdapter)
        >>> adapter = create_adapter("my_adapter")
    """
    if not issubclass(adapter_class, BaseAIAdapter):
        raise TypeError(f"{adapter_class} must inherit from BaseAIAdapter")
    
    ADAPTER_REGISTRY[name.lower()] = adapter_class


def list_adapters() -> list:
    """
    Get list of available adapter names.
    
    Returns:
        List of registered adapter names
    """
    return list(ADAPTER_REGISTRY.keys())


__all__ = [
    "BaseAIAdapter",
    "MockAdapter",
    "CustomAdapter",
    "create_adapter",
    "register_adapter",
    "list_adapters",
    "ADAPTER_REGISTRY",
]
