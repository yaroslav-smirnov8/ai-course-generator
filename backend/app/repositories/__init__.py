# repositories/__init__.py
from .user import UserRepository
from .generation import GenerationRepository

__all__ = [
    'UserRepository',
    'GenerationRepository'
]