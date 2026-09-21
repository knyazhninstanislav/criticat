# worker.py
from PySide6.QtCore import QThread, Signal
from typing import List

from desktop.database.database import DatabaseManager
from lis.base import LisProvider
from services.critical_filter import CriticalFilterService


class CheckWorker(QThread):
    finished = Signal(list)
    error_occurred = Signal(str)

    def __init__(
        self,
        lis_provider: LisProvider,
        db_manager: DatabaseManager,
        test_names: List[str],
        excluded_ids: List[int],
        test_settings: dict = None
    ):
        super().__init__()
        self.lis_provider = lis_provider
        self.db_manager = db_manager
        self.test_names = test_names
        self.excluded_ids = excluded_ids
        self.test_settings = test_settings or {}
        self.critical_filter = CriticalFilterService()

    def run(self):
        """Выполнение проверки в фоновом потоке"""
        try:
            # 1. Проверяем соединение с ЛИС
            if not self.lis_provider.is_connected():
                if not self.lis_provider.connect():
                    self.error_occurred.emit("Не удалось подключиться к ЛИС")
                    self.finished.emit([])
                    return

            # 2. Читаем сырые данные из ЛИС
            raw_results = self.lis_provider.get_results_for_tests(
                self.test_names,
                self.excluded_ids
            )

            # 3. Фильтруем критичные
            critical = self.critical_filter.filter_critical(
                raw_results,
                self.test_settings
            )

            # 4. Отдаём результат
            self.finished.emit(critical)

        except Exception as e:
            self.error_occurred.emit(f"Ошибка при проверке: {str(e)}")
            self.finished.emit([])