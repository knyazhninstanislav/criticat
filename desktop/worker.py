from PySide6.QtCore import QThread, Signal
from typing import List, Dict, Any
from database import DatabaseManager


class CheckWorker(QThread):
    finished = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, db_path: str, test_names: List[str],
                 threshold_percent: float, excluded_ids: List[int],
                 test_settings: dict = None):
        super().__init__()
        self.db_path = db_path
        self.test_names = test_names
        self.threshold_percent = threshold_percent
        self.excluded_ids = excluded_ids
        self.test_settings = test_settings or {}

    def run(self):
        """Выполнение проверки в фоновом потоке"""
        db_manager = DatabaseManager(self.db_path)

        try:
            if not db_manager.connect():
                self.error_occurred.emit("Не удалось подключиться к БД")
                self.finished.emit([])
                return

            results = db_manager.get_pathological_results_with_settings(
                self.test_names,
                self.threshold_percent,
                self.excluded_ids,
                self.test_settings
            )
            self.finished.emit(results)

        except Exception as e:
            self.error_occurred.emit(f"Ошибка при проверке: {str(e)}")
            self.finished.emit([])
        finally:
            db_manager.disconnect()