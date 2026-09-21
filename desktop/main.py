# main.py
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, QSettings

from ui.main_window import MainWindow
from desktop.ui.splash_screen import SplashController
from desktop.ui.themes import ThemeController
from desktop.database.database import DatabaseManager
from lis.factory import LisProviderFactory


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # ===== ТЕМА =====
    theme_controller = ThemeController(app)
    app_settings = QSettings('CritiCat', 'LabMonitor')
    saved_theme = app_settings.value('theme', 'light')
    theme_controller.apply_theme(saved_theme)

    # ===== СПЛЭШ =====
    splash_controller = SplashController()
    splash = splash_controller.show(duration_ms=5000)

    # ===== СВОЯ БД =====
    db_manager = DatabaseManager()

    # ===== ПРОВАЙДЕР ЛИС =====
    lis_provider_type = app_settings.value('lis_provider', 'mock')
    lis_db_path = app_settings.value('lis_db_path', 'db\mock_lis.db')

    try:
        lis_provider = LisProviderFactory.create(
            provider_type=lis_provider_type,
            db_path=lis_db_path
        )
    except Exception as e:
        QMessageBox.critical(None, "Ошибка", f"Не удалось создать провайдер ЛИС: {e}")
        splash_controller.close()
        sys.exit(1)

    # ===== ИНИЦИАЛИЗАЦИЯ =====
    def initialize_app():
        try:
            # 1. Своя БД
            if not db_manager.connect():
                QMessageBox.critical(None, "Ошибка",
                                     "Не удалось подключиться к базе данных CritiCat")
                splash_controller.close()
                sys.exit(1)

            # 2. ЛИС
            if not lis_provider.connect():
                QMessageBox.critical(None, "Ошибка",
                                     "Не удалось подключиться к ЛИС")
                splash_controller.close()
                sys.exit(1)

            # 3. Сиды для мока
            if lis_provider_type == 'mock':
                try:
                    lis_provider.seed_demo_data()
                except Exception as e:
                    print(f"Не удалось залить сиды: {e}")

            # 4. Главное окно — ПЕРЕДАЁМ провайдер!
            window = MainWindow(
                theme_controller=theme_controller,
                app_settings=app_settings,
                db_manager=db_manager,
                lis_provider=lis_provider        # ← КЛЮЧЕВАЯ СТРОКА
            )

            splash_controller.close()
            window.show()

        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Ошибка инициализации: {e}")
            splash_controller.close()
            sys.exit(1)

    QTimer.singleShot(2000, initialize_app)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()