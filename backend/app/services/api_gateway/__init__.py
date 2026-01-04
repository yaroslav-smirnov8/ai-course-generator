"""
API Gateway for unified access to various AI providers.

Supports fallback logic:
1. First fallback to models within provider
2. Then fallback to other providers

Architecture:
- DirectProvider: Direct calls to AI services (primary)
- NetlifyProvider: For images only
"""

from .gateway import APIGateway
from .providers import BaseProvider, DirectProvider, NetlifyProvider
from .config import get_provider_config, PROVIDER_PRIORITIES
from .models import APIRequest, APIResponse, ProviderConfig, ModelConfig

__all__ = [
    'APIGateway',
    'BaseProvider',
    'DirectProvider',
    'NetlifyProvider',
    'get_provider_config',
    'PROVIDER_PRIORITIES',
    'APIRequest',
    'APIResponse',
    'ProviderConfig',
    'ModelConfig'
]
