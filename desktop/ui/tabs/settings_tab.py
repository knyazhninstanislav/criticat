from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QSpinBox, QPushButton, QGroupBox,
                               QLabel, QFrame, QScrollArea, QComboBox, QMessageBox,
                               QCheckBox, QTextEdit)
from PySide6.QtCore import Qt
from database.models import Settings


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

        label_style = "color: #2c3e50; font-size: 11px; background-color: transparent;"

        # ========== Группа параметров проверки ==========
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
        check_layout.addRow("", self.test_settings_btn)

        check_group.setLayout(check_layout)
        layout.addWidget(check_group)

        # ========== Группа настроек VDS сервера ==========
        vds_group = QGroupBox("🖥️ Настройки VDS сервера")
        vds_group.setStyleSheet("""
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
        vds_layout = QFormLayout()
        vds_layout.setSpacing(8)
        vds_layout.setContentsMargins(5, 5, 5, 5)
        vds_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # Чекбокс включения
        self.server_enabled_cb = QCheckBox("Включить отправку уведомлений через VDS")
        self.server_enabled_cb.setChecked(False)
        self.server_enabled_cb.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
                font-size: 12px;
                font-weight: bold;
                spacing: 5px;
            }
        """)
        vds_layout.addRow("", self.server_enabled_cb)

        # URL
        url_label = QLabel("URL сервера:")
        url_label.setStyleSheet(label_style)

        self.server_url_input = QLineEdit()
        self.server_url_input.setPlaceholderText("http://176.98.181.45:26000")
        self.server_url_input.setMinimumHeight(30)
        self.server_url_input.setStyleSheet(self._get_input_style())
        vds_layout.addRow(url_label, self.server_url_input)

        # API ключ
        api_key_label = QLabel("API ключ:")
        api_key_label.setStyleSheet(label_style)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Введите API ключ")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setMinimumHeight(30)
        self.api_key_input.setStyleSheet(self._get_input_style())
        vds_layout.addRow(api_key_label, self.api_key_input)

        # Интервал опроса
        poll_label = QLabel("Интервал опроса:")
        poll_label.setStyleSheet(label_style)

        self.poll_interval_spin = QSpinBox()
        self.poll_interval_spin.setRange(10, 300)
        self.poll_interval_spin.setValue(30)
        self.poll_interval_spin.setSuffix(" сек")
        self.poll_interval_spin.setMinimumHeight(30)
        self.poll_interval_spin.setStyleSheet(self._get_input_style())
        vds_layout.addRow(poll_label, self.poll_interval_spin)

        # Кнопка проверки соединения
        self.test_server_btn = QPushButton("🔌 Проверить соединение")
        self.test_server_btn.clicked.connect(self.test_server_connection)
        self.test_server_btn.setMinimumHeight(35)
        self.test_server_btn.setMaximumWidth(200)
        self.test_server_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 8px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.test_server_btn)
        btn_layout.addStretch()
        vds_layout.addRow("", btn_layout)

        # Кнопка сохранения настроек VDS
        self.save_vds_btn = QPushButton("💾 Сохранить настройки VDS")
        self.save_vds_btn.clicked.connect(self.save_vds_settings)
        self.save_vds_btn.setMinimumHeight(38)
        self.save_vds_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 5px;
                padding: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        vds_layout.addRow("", self.save_vds_btn)

        # Лог
        log_label = QLabel("📋 Лог:")
        log_label.setStyleSheet(label_style)
        vds_layout.addRow(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(80)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #fafbfc;
                color: #2c3e50;
                padding: 5px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
        """)
        vds_layout.addRow(self.log_text)

        vds_group.setLayout(vds_layout)
        layout.addWidget(vds_group)

        # ========== Группа настроек темы ==========
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

        # ========== Кнопка применения общих настроек ==========
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

    def _get_input_style(self):
        """Стиль для полей ввода"""
        return """
            QLineEdit, QSpinBox {
                padding: 5px 10px;
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #3498db;
                background-color: #f7f9fc;
            }
        """

    def _on_theme_changed(self, index):
        """Обработчик изменения темы"""
        theme_name = self.theme_combo.currentData()

        if hasattr(self.main_window, 'theme_controller') and self.main_window.theme_controller:
            try:
                self.main_window.theme_controller.apply_theme(theme_name)

                if hasattr(self.main_window, 'app_settings') and self.main_window.app_settings:
                    self.main_window.app_settings.setValue('theme', theme_name)

                if hasattr(self.main_window, 'theme_btn'):
                    if theme_name == 'dark':
                        self.main_window.theme_btn.setText("☀️ Светлая тема")
                    else:
                        self.main_window.theme_btn.setText("🌙 Темная тема")

                if hasattr(self.main_window, '_update_tabs_theme'):
                    self.main_window._update_tabs_theme()

                self.main_window.log_message(f"Тема изменена на: {'темную' if theme_name == 'dark' else 'светлую'}")
            except Exception as e:
                print(f"Ошибка применения темы: {e}")

    def open_test_settings(self):
        """Открытие окна настройки тестов"""
        from ui.dialogs.test_settings_dialog import TestSettingsDialog

        if not self.main_window.db_manager.is_connected():
            QMessageBox.warning(self, "Предупреждение", "Нет подключения к БД")
            return

        saved_settings = self.main_window.db_manager.load_test_settings()

        if not saved_settings:
            test_names = self.main_window.lis_provider.get_all_test_names()
            ref_values = self.main_window.lis_provider.get_test_reference_values()

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
            self,
            lis_provider=self.main_window.lis_provider  # ← передаём провайдер
        )

        if dialog.exec() == TestSettingsDialog.Accepted:
            test_settings = dialog.get_settings()
            self.main_window.test_settings = test_settings

            monitored_tests = [
                name for name, config in test_settings.items()
                if config.get('monitored', False)
            ]

            self.main_window.settings.monitored_tests = monitored_tests
            self.main_window.log_message(f"Обновлены настройки тестов ({len(monitored_tests)} тестов)")

    def test_server_connection(self):
        """Проверка соединения и авторизации VDS"""
        url = self.server_url_input.text().strip()
        api_key = self.api_key_input.text().strip()

        if not url:
            QMessageBox.warning(self, "Предупреждение", "Введите URL сервера")
            return

        if not api_key:
            QMessageBox.warning(self, "Предупреждение", "Введите API ключ")
            return

        from server_client import ServerClient
        temp_client = ServerClient()
        temp_client.set_server_url(url)
        temp_client.set_api_key(api_key)

        success, message = temp_client.test_connection()

        if success:
            QMessageBox.information(self, "Успех", message)
            self.log_text.append(f"✅ {message}")
        else:
            QMessageBox.critical(self, "Ошибка", message)
            self.log_text.append(f"❌ {message}")

        temp_client.close()

    def save_vds_settings(self):
        """Сохранение настроек VDS"""
        try:
            url = self.server_url_input.text().strip()

            if self.server_enabled_cb.isChecked() and not url:
                QMessageBox.warning(self, "Предупреждение", "Введите URL сервера")
                return

            if hasattr(self.main_window, 'save_server_settings'):
                self.main_window.save_server_settings()

            if self.server_enabled_cb.isChecked() and url:
                try:
                    from server_client import ServerClient
                    temp_client = ServerClient(url, self.api_key_input.text().strip())
                    success, message = temp_client.test_connection()
                    temp_client.close()

                    if success:
                        self.log_text.append(f"✅ {message}")
                        QMessageBox.information(self, "Успех", "Настройки сохранены, соединение установлено")
                    else:
                        self.log_text.append(f"❌ {message}")
                        QMessageBox.warning(self, "Предупреждение",
                                            f"Настройки сохранены, но соединение не установлено:\n{message}")
                except Exception as e:
                    self.log_text.append(f"❌ Ошибка проверки: {e}")
            else:
                QMessageBox.information(self, "Успех", "Настройки сохранены")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")

    def get_settings(self) -> Settings:
        """Получение текущих настроек"""
        # Берём db_path из существующих настроек, если есть
        current_db_path = "../desktop/db/criticat.db"
        if hasattr(self.main_window, 'settings') and self.main_window.settings:
            current_db_path = self.main_window.settings.db_path or "../desktop/db/criticat.db"

        return Settings(
            db_path=current_db_path,
            check_interval=self.interval_spin.value(),
            threshold_percent=0,
            monitored_tests=self.main_window.settings.monitored_tests
            if hasattr(self.main_window, 'settings') else []
        )

    def get_server_settings(self) -> dict:
        """Получение настроек сервера"""
        return {
            'enabled': self.server_enabled_cb.isChecked(),
            'url': self.server_url_input.text().strip(),
            'api_key': self.api_key_input.text().strip(),
            'poll_interval': self.poll_interval_spin.value(),
        }

    def set_server_settings(self, settings: dict):
        """Установка настроек сервера"""
        self.server_enabled_cb.setChecked(settings.get('enabled', False))
        self.server_url_input.setText(settings.get('url', ''))
        self.api_key_input.setText(settings.get('api_key', ''))
        self.poll_interval_spin.setValue(settings.get('poll_interval', 30))