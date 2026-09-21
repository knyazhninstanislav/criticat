# lis/factory.py
from .base import LisProvider
from .mock_provider import MockLisProvider


class LisProviderFactory:
    """Фабрика провайдеров ЛИС."""

    @staticmethod
    def create(provider_type: str, **kwargs) -> LisProvider:
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
            return MockLisProvider(**kwargs)

        # Когда появятся реальные провайдеры — добавить сюда:
        # elif provider_type == 'sqlite':
        #     from .sqlite_lis_provider import SqliteLisProvider
        #     return SqliteLisProvider(**kwargs)
        #
        # elif provider_type == 'mssql':
        #     from .mssql_lis_provider import MsSqlLisProvider
        #     return MsSqlLisProvider(**kwargs)

        raise ValueError(f"Неизвестный тип ЛИС: {provider_type}")