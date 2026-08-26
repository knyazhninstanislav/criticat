from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QSpinBox, QPushButton, QGroupBox,
                               QLabel, QFrame, QScrollArea, QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from models import Settings


class SettingsTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: transparent;")

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)

        # Заголовок
        header = QLabel("⚙️ Настройки")
        header.setStyleSheet("""
            font-size: 15px; 
            font-weight: bold; 
            color: #2196F3; 
            padding: 5px;
            background-color: transparent;
        """)
        layout.addWidget(header)

        # Группа настроек подключения к БД
        db_group = QGroupBox("🔗 Подключение к БД")
        db_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                margin-top: 8px;
                padding: 16px 10px 10px 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2196F3;
                background-color: #ffffff;
            }
        """)
        db_layout = QFormLayout()
        db_layout.setSpacing(6)
        db_layout.setContentsMargins(5, 5, 5, 5)

        label_style = "color: #2c3e50; font-size: 11px; background-color: transparent;"

        path_label = QLabel("Путь к БД:")
        path_label.setStyleSheet(label_style)

        self.db_path_input = QLineEdit("testbase")
        self.db_path_input.setPlaceholderText("Путь к файлу БД")
        self.db_path_input.setMaximumHeight(30)
        self.db_path_input.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #f7f9fc;
            }
        """)
        db_layout.addRow(path_label, self.db_path_input)

        login_label = QLabel("Логин:")
        login_label.setStyleSheet(label_style)

        self.db_login_input = QLineEdit()
        self.db_login_input.setPlaceholderText("Не используется")
        self.db_login_input.setEnabled(False)
        self.db_login_input.setMaximumHeight(30)
        self.db_login_input.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #ecf0f1;
                color: #7f8c8d;
                font-size: 12px;
            }
        """)
        db_layout.addRow(login_label, self.db_login_input)

        pass_label = QLabel("Пароль:")
        pass_label.setStyleSheet(label_style)

        self.db_password_input = QLineEdit()
        self.db_password_input.setPlaceholderText("Не используется")
        self.db_password_input.setEchoMode(QLineEdit.Password)
        self.db_password_input.setEnabled(False)
        self.db_password_input.setMaximumHeight(30)
        self.db_password_input.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #ecf0f1;
                color: #7f8c8d;
                font-size: 12px;
            }
        """)
        db_layout.addRow(pass_label, self.db_password_input)

        db_group.setLayout(db_layout)
        layout.addWidget(db_group)

        # Группа параметров проверки
        check_group = QGroupBox("⏱️ Параметры проверки")
        check_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                margin-top: 8px;
                padding: 16px 10px 10px 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2196F3;
                background-color: #ffffff;
            }
        """)
        check_layout = QFormLayout()
        check_layout.setSpacing(6)
        check_layout.setContentsMargins(5, 5, 5, 5)

        interval_label = QLabel("Периодичность:")
        interval_label.setStyleSheet(label_style)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setValue(5)
        self.interval_spin.setSuffix(" мин.")
        self.interval_spin.setMaximumHeight(30)
        self.interval_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px 10px;
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 12px;
            }
            QSpinBox:focus {
                border-color: #3498db;
                background-color: #f7f9fc;
            }
        """)
        check_layout.addRow(interval_label, self.interval_spin)

        # Кнопка настройки тестов
        tests_button_layout = QHBoxLayout()

        self.test_settings_btn = QPushButton("🧪 Настроить отслеживаемые тесты")
        self.test_settings_btn.clicked.connect(self.open_test_settings)
        self.test_settings_btn.setMinimumHeight(35)
        self.test_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 8px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        tests_button_layout.addWidget(self.test_settings_btn)
        tests_button_layout.addStretch()

        check_layout.addRow("", self.test_settings_btn)

        check_group.setLayout(check_layout)
        layout.addWidget(check_group)

        # Группа настроек темы
        theme_group = QGroupBox("🎨 Тема оформления")
        theme_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                margin-top: 8px;
                padding: 16px 10px 10px 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2196F3;
                background-color: #ffffff;
            }
        """)
        theme_layout = QHBoxLayout()
        theme_layout.setSpacing(10)

        theme_label = QLabel("Тема:")
        theme_label.setStyleSheet(label_style)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("☀️ Светлая", "light")
        self.theme_combo.addItem("🌙 Темная", "dark")
        self.theme_combo.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 11px;
                min-height: 25px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
        """)

        # Устанавливаем текущую тему
        if hasattr(self.main_window, 'theme_controller') and self.main_window.theme_controller:
            try:
                current_theme = self.main_window.theme_controller.get_current_theme()
                index = self.theme_combo.findData(current_theme)
                if index >= 0:
                    self.theme_combo.setCurrentIndex(index)
            except:
                pass

        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)

        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()

        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        # Группа информации
        info_group = QGroupBox("ℹ️ Информация")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                margin-top: 8px;
                padding: 16px 10px 10px 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2196F3;
                background-color: #ffffff;
            }
        """)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        info_layout.setContentsMargins(5, 5, 5, 5)

        info_text = QLabel(
            "CritiCat - система мониторинга критических значений\n"
            "лабораторных исследований\n\n"
            "Версия: 1.0.0\n"
            "Лицензия: MIT"
        )
        info_text.setStyleSheet("""
            color: #7f8c8d;
            font-size: 11px;
            background-color: transparent;
            line-height: 1.5;
        """)
        info_layout.addWidget(info_text)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Кнопка применения
        apply_frame = QFrame()
        apply_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f5e9;
                border: 1px solid #a5d6a7;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        apply_layout = QVBoxLayout()
        apply_layout.setContentsMargins(5, 5, 5, 5)

        self.apply_btn = QPushButton("✅ Применить настройки")
        self.apply_btn.setMaximumHeight(38)
        self.apply_btn.clicked.connect(self.main_window.apply_settings)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)

        apply_layout.addWidget(self.apply_btn)
        apply_frame.setLayout(apply_layout)
        layout.addWidget(apply_frame)

        layout.addStretch()

        scroll_widget.setLayout(layout)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def _on_theme_changed(self, index):
        """Обработчик изменения темы"""
        theme_name = self.theme_combo.currentData()

        if hasattr(self.main_window, 'theme_controller') and self.main_window.theme_controller:
            try:
                self.main_window.theme_controller.apply_theme(theme_name)

                # Сохраняем тему
                if hasattr(self.main_window, 'app_settings') and self.main_window.app_settings:
                    self.main_window.app_settings.setValue('theme', theme_name)

                # Обновляем кнопку в статус-баре
                if hasattr(self.main_window, 'theme_btn'):
                    if theme_name == 'dark':
                        self.main_window.theme_btn.setText("☀️ Светлая тема")
                    else:
                        self.main_window.theme_btn.setText("🌙 Темная тема")

                # Обновляем тему для всех вкладок
                if hasattr(self.main_window, '_update_tabs_theme'):
                    self.main_window._update_tabs_theme()

                self.main_window.log_message(f"Тема изменена на: {'темную' if theme_name == 'dark' else 'светлую'}")
            except Exception as e:
                print(f"Ошибка применения темы: {e}")

    def open_test_settings(self):
        """Открытие окна настройки тестов"""
        from ui.test_settings_dialog import TestSettingsDialog

        # Проверяем подключение к БД
        if not self.main_window.db_manager.is_connected():
            QMessageBox.warning(self, "Предупреждение", "Нет подключения к БД")
            return

        # Загружаем сохраненные настройки
        saved_settings = self.main_window.db_manager.load_test_settings()

        # Если настроек нет, но есть тесты в БД, создаем пустые настройки
        if not saved_settings:
            test_names = self.main_window.db_manager.get_all_test_names()
            ref_values = self.main_window.db_manager.get_test_reference_values()

            for test_name in test_names:
                saved_settings[test_name] = {
                    'monitored': False,
                    'monitor_type': 'both',
                    'ref_lower': ref_values.get(test_name, {}).get('ref_lower', 0),
                    'ref_upper': ref_values.get(test_name, {}).get('ref_upper', 0)
                }

        dialog = TestSettingsDialog(
            self.main_window.db_manager,
            saved_settings,
            self
        )

        if dialog.exec() == TestSettingsDialog.Accepted:
            # Получаем обновленные настройки
            test_settings = dialog.get_settings()

            # Сохраняем в главном окне
            self.main_window.test_settings = test_settings

            # Обновляем мониторируемые тесты
            monitored_tests = [
                name for name, config in test_settings.items()
                if config.get('monitored', False)
            ]

            self.main_window.settings.monitored_tests = monitored_tests

            self.main_window.log_message(f"Обновлены настройки тестов ({len(monitored_tests)} тестов)")
    def get_settings(self) -> Settings:
        """Получение текущих настроек"""
        return Settings(
            db_path=self.db_path_input.text(),
            check_interval=self.interval_spin.value(),
            threshold_percent=0,  # Больше не используется
            monitored_tests=self.main_window.settings.monitored_tests if hasattr(self.main_window, 'settings') else []
        )