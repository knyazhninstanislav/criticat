# providers/__init__.py
from desktop.providers.base import BaseProvider, BaseResult
from desktop.providers.factory import ProviderFactory

__all__ = ['BaseProvider', 'BaseResult', 'ProviderFactory']