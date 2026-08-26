import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QIcon, QPalette, QColor
from ui.main_window import MainWindow
from splash_screen import CritiCatSplashScreen, SplashController
from themes import ThemeController
from database import DatabaseManager


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Создаем контроллер тем
    theme_controller = ThemeController(app)

    # Загружаем сохраненную тему
    app_settings = QSettings('CritiCat', 'LabMonitor')
    saved_theme = app_settings.value('theme', 'light')
    theme_controller.apply_theme(saved_theme)

    # Показываем сплэш-скрин
    splash_controller = SplashController()
    splash = splash_controller.show(duration_ms=5000)

    # Инициализация БД
    db_manager = DatabaseManager()

    # Имитируем загрузку
    def initialize_app():
        try:
            if not db_manager.connect():
                QMessageBox.critical(None, "Ошибка", "Не удалось подключиться к базе данных")
                splash_controller.close()
                sys.exit(1)

            # Создаем главное окно с передачей theme_controller и app_settings
            window = MainWindow(theme_controller=theme_controller, app_settings=app_settings)

            # Закрываем сплэш-скрин
            splash_controller.close()

            # Показываем главное окно
            window.show()

        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка инициализации: {e}")
            splash_controller.close()
            sys.exit(1)

    # Запускаем инициализацию после задержки
    QTimer.singleShot(2000, initialize_app)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()