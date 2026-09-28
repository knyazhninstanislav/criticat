# providers/factory.py
from .base import BaseProvider
from .mock_lis_provider import MockBaseProvider


class ProviderFactory:
    """Фабрика провайдеров ЛИС."""

    @staticmethod
    def create(provider_type: str, **kwargs) -> BaseProvider:
        """
        Создать провайдер ЛИС по типу.

        Args:
            provider_type: 'mock' | 'sqlite' | 'mssql' | 'oracle' | ...
            **kwargs: параметры для конкретного провайдера

        Returns:
            Экземпляр LisProvider
        """
        provider_type = (provider_type or 'mock').lower()

        if provider_type == 'mock':
            return MockBaseProvider(**kwargs)

        if provider_type == 'swelab_com':
            from .swelab_com_provider import SwelabComProvider
            return SwelabComProvider(**kwargs)

        # Когда появятся реальные провайдеры — добавить сюда:
        # elif provider_type == 'sqlite':
        #     from .sqlite_lis_provider import SqliteLisProvider
        #     return SqliteLisProvider(**kwargs)
        #
        # elif provider_type == 'mssql':
        #     from .mssql_lis_provider import MsSqlLisProvider
        #     return MsSqlLisProvider(**kwargs)

        raise ValueError(f"Неизвестный тип ЛИС: {provider_type}")