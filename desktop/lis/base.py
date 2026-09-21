# lis/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class LisResult:
    """Сырой результат из ЛИС — универсальная структура"""
    id: int
    ids: int                    # ID пациента
    full_name: str
    department: str
    test_name: str
    result_value: float
    ref_lower: Optional[float]
    ref_upper: Optional[float]


class LisProvider(ABC):
    """
    Абстрактный провайдер ЛИС.

    Любая конкретная ЛИС (Mock, SQLite, MSSQL, Oracle...) должна
    реализовать этот интерфейс. Остальная система работает
    ТОЛЬКО с этим интерфейсом и не знает, какая ЛИС под капотом.
    """

    @abstractmethod
    def connect(self) -> bool:
        """Установить соединение с ЛИС"""
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Закрыть соединение"""
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """Проверить соединение"""
        ...

    @abstractmethod
    def get_all_test_names(self) -> List[str]:
        """Получить список всех уникальных тестов"""
        ...

    @abstractmethod
    def get_test_reference_values(self) -> Dict[str, Dict[str, float]]:
        """Получить референсные значения для тестов"""
        ...

    @abstractmethod
    def get_results_for_tests(
        self,
        test_names: List[str],
        excluded_ids: List[int]
    ) -> List[LisResult]:
        """
        Получить сырые результаты по указанным тестам.
        Исключить excluded_ids.

        ВАЖНО: этот метод НЕ фильтрует по критичности!
        """
        ...