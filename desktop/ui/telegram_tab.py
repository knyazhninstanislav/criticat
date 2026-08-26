from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QLabel, QGroupBox,
                               QListWidget, QListWidgetItem, QFrame,
                               QFormLayout, QMessageBox, QTextEdit,
                               QCheckBox, QSpinBox, QScrollArea)
from PySide6.QtCore import Qt
from server_client import ServerClient


class TelegramTab(QWidget):
    """Вкладка настройки уведомлений через VDS сервер"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        # Основной вертикальный layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Scroll area для всех компонентов
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f0f2f5;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
        """)

        # Контейнер внутри скролла
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setSpacing(10)
        container_layout.setContentsMargins(0, 0, 5, 5)

        # Заголовок
        header = QLabel("📱 Уведомления через VDS сервер")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2196F3;
            padding: 5px;
            background-color: transparent;
        """)
        container_layout.addWidget(header)

        # Информация
        info = QLabel(
            "Уведомления отправляются через промежуточный VDS сервер.\n"
            "Десктоп отправляет обезличенные данные на сервер,\n"
            "сервер отправляет их в Telegram и обрабатывает подтверждения."
        )
        info.setStyleSheet("""
            color: #7f8c8d;
            font-size: 11px;
            background-color: transparent;
            line-height: 1.5;
        """)
        info.setWordWrap(True)
        container_layout.addWidget(info)

        # ========== ГРУППА VDS СЕРВЕРА ==========
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

        # Включение отправки
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

        # URL сервера
        url_label = QLabel("URL сервера:")
        url_label.setStyleSheet("color: #2c3e50; font-size: 11px; background-color: transparent;")
        url_label.setFixedHeight(30)

        self.server_url_input = QLineEdit()
        self.server_url_input.setPlaceholderText("http://176.98.181.45:26000")
        self.server_url_input.setMinimumHeight(30)
        self.server_url_input.setStyleSheet(self._get_input_style())
        vds_layout.addRow(url_label, self.server_url_input)

        # API ключ
        api_key_label = QLabel("API ключ:")
        api_key_label.setStyleSheet("color: #2c3e50; font-size: 11px; background-color: transparent;")
        api_key_label.setFixedHeight(30)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Введите API ключ")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setMinimumHeight(30)
        self.api_key_input.setStyleSheet(self._get_input_style())
        vds_layout.addRow(api_key_label, self.api_key_input)

        # Интервал опроса
        poll_label = QLabel("Интервал опроса:")
        poll_label.setStyleSheet("color: #2c3e50; font-size: 11px; background-color: transparent;")
        poll_label.setFixedHeight(30)

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

        vds_group.setLayout(vds_layout)
        container_layout.addWidget(vds_group)

        # ========== ГРУППА ПОЛЬЗОВАТЕЛЕЙ ==========
        users_group = QGroupBox("👥 Пользователи Telegram")
        users_group.setStyleSheet("""
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
        users_layout = QVBoxLayout()
        users_layout.setSpacing(8)
        users_layout.setContentsMargins(5, 5, 5, 5)

        # Поле для добавления пользователя
        add_user_layout = QHBoxLayout()
        add_user_layout.setSpacing(5)

        self.new_user_input = QLineEdit()
        self.new_user_input.setPlaceholderText("Введите chat_id пользователя")
        self.new_user_input.setMinimumHeight(30)
        self.new_user_input.setStyleSheet(self._get_input_style())
        add_user_layout.addWidget(self.new_user_input)

        self.add_user_btn = QPushButton("➕ Добавить")
        self.add_user_btn.clicked.connect(self.add_user)
        self.add_user_btn.setMinimumHeight(30)
        self.add_user_btn.setMaximumWidth(120)
        self.add_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
                padding: 5px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        add_user_layout.addWidget(self.add_user_btn)

        users_layout.addLayout(add_user_layout)

        # Список пользователей
        self.users_list = QListWidget()
        self.users_list.setMinimumHeight(100)
        self.users_list.setMaximumHeight(150)
        self.users_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #ffffff;
                padding: 4px;
                font-size: 11px;
                color: #2c3e50;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 3px;
                margin: 1px 0px;
            }
            QListWidget::item:selected {
                background-color: #ffebee;
                color: #2c3e50;
            }
        """)
        users_layout.addWidget(self.users_list)

        # Кнопки управления пользователями
        user_buttons_layout = QHBoxLayout()
        user_buttons_layout.setSpacing(5)

        self.remove_user_btn = QPushButton("🗑️ Удалить")
        self.remove_user_btn.clicked.connect(self.remove_user)
        self.remove_user_btn.setMinimumHeight(28)
        self.remove_user_btn.setMaximumWidth(120)
        self.remove_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                font-size: 10px;
                border-radius: 4px;
                padding: 5px 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        self.refresh_users_btn = QPushButton("🔄 Обновить")
        self.refresh_users_btn.clicked.connect(self.load_users)
        self.refresh_users_btn.setMinimumHeight(28)
        self.refresh_users_btn.setMaximumWidth(120)
        self.refresh_users_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                font-size: 10px;
                border-radius: 4px;
                padding: 5px 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)

        user_buttons_layout.addWidget(self.remove_user_btn)
        user_buttons_layout.addWidget(self.refresh_users_btn)
        user_buttons_layout.addStretch()

        users_layout.addLayout(user_buttons_layout)

        users_group.setLayout(users_layout)
        container_layout.addWidget(users_group)

        # ========== ГРУППА MQTT ==========
        mqtt_group = QGroupBox("📨 Настройки MQTT")
        mqtt_group.setStyleSheet("""
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
        mqtt_layout = QFormLayout()
        mqtt_layout.setSpacing(8)
        mqtt_layout.setContentsMargins(5, 5, 5, 5)
        mqtt_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.mqtt_enabled_cb = QCheckBox("Включить отправку через MQTT")
        self.mqtt_enabled_cb.setChecked(False)
        self.mqtt_enabled_cb.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
                font-size: 12px;
                font-weight: bold;
                spacing: 5px;
            }
        """)
        mqtt_layout.addRow("", self.mqtt_enabled_cb)

        # Хост
        mqtt_host_label = QLabel("Хост брокера:")
        mqtt_host_label.setStyleSheet("color: #2c3e50; font-size: 11px; background-color: transparent;")
        mqtt_host_label.setFixedHeight(30)

        self.mqtt_host_input = QLineEdit()
        self.mqtt_host_input.setPlaceholderText("localhost или IP адрес")
        self.mqtt_host_input.setMinimumHeight(30)
        self.mqtt_host_input.setStyleSheet(self._get_input_style())
        mqtt_layout.addRow(mqtt_host_label, self.mqtt_host_input)

        # Порт
        mqtt_port_label = QLabel("Порт:")
        mqtt_port_label.setStyleSheet("color: #2c3e50; font-size: 11px; background-color: transparent;")
        mqtt_port_label.setFixedHeight(30)

        self.mqtt_port_spin = QSpinBox()
        self.mqtt_port_spin.setRange(1, 65535)
        self.mqtt_port_spin.setValue(1883)
        self.mqtt_port_spin.setMinimumHeight(30)
        self.mqtt_port_spin.setStyleSheet(self._get_input_style())
        mqtt_layout.addRow(mqtt_port_label, self.mqtt_port_spin)

        # Имя пользователя
        mqtt_user_label = QLabel("Имя пользователя:")
        mqtt_user_label.setStyleSheet("color: #2c3e50; font-size: 11px; background-color: transparent;")
        mqtt_user_label.setFixedHeight(30)

        self.mqtt_username_input = QLineEdit()
        self.mqtt_username_input.setPlaceholderText("(опционально)")
        self.mqtt_username_input.setMinimumHeight(30)
        self.mqtt_username_input.setStyleSheet(self._get_input_style())
        mqtt_layout.addRow(mqtt_user_label, self.mqtt_username_input)

        # Пароль
        mqtt_pass_label = QLabel("Пароль:")
        mqtt_pass_label.setStyleSheet("color: #2c3e50; font-size: 11px; background-color: transparent;")
        mqtt_pass_label.setFixedHeight(30)

        self.mqtt_password_input = QLineEdit()
        self.mqtt_password_input.setPlaceholderText("(опционально)")
        self.mqtt_password_input.setEchoMode(QLineEdit.Password)
        self.mqtt_password_input.setMinimumHeight(30)
        self.mqtt_password_input.setStyleSheet(self._get_input_style())
        mqtt_layout.addRow(mqtt_pass_label, self.mqtt_password_input)

        # Интервал опроса
        mqtt_poll_label = QLabel("Интервал опроса:")
        mqtt_poll_label.setStyleSheet("color: #2c3e50; font-size: 11px; background-color: transparent;")
        mqtt_poll_label.setFixedHeight(30)

        self.mqtt_poll_interval_spin = QSpinBox()
        self.mqtt_poll_interval_spin.setRange(10, 300)
        self.mqtt_poll_interval_spin.setValue(30)
        self.mqtt_poll_interval_spin.setSuffix(" сек")
        self.mqtt_poll_interval_spin.setMinimumHeight(30)
        self.mqtt_poll_interval_spin.setStyleSheet(self._get_input_style())
        mqtt_layout.addRow(mqtt_poll_label, self.mqtt_poll_interval_spin)

        # Кнопка проверки
        self.test_mqtt_btn = QPushButton("🔌 Проверить соединение MQTT")
        self.test_mqtt_btn.clicked.connect(self.test_mqtt_connection)
        self.test_mqtt_btn.setMinimumHeight(35)
        self.test_mqtt_btn.setMaximumWidth(200)
        self.test_mqtt_btn.setStyleSheet("""
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
        mqtt_btn_layout = QHBoxLayout()
        mqtt_btn_layout.addWidget(self.test_mqtt_btn)
        mqtt_btn_layout.addStretch()
        mqtt_layout.addRow("", mqtt_btn_layout)

        mqtt_group.setLayout(mqtt_layout)
        container_layout.addWidget(mqtt_group)

        # ========== ЛОГ ==========
        log_group = QGroupBox("📋 Лог")
        log_group.setStyleSheet("""
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
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(5, 5, 5, 5)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(80)
        self.log_text.setMaximumHeight(100)
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
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        container_layout.addWidget(log_group)

        # ========== КНОПКА СОХРАНЕНИЯ ==========
        self.save_btn = QPushButton("💾 Сохранить настройки")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setStyleSheet("""
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
        container_layout.addWidget(self.save_btn)

        container_layout.addStretch()

        container.setLayout(container_layout)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

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

    def test_mqtt_connection(self):
        """Проверка MQTT соединения"""
        host = self.mqtt_host_input.text().strip()
        port = self.mqtt_port_spin.value()
        username = self.mqtt_username_input.text().strip()
        password = self.mqtt_password_input.text().strip()

        if not host:
            QMessageBox.warning(self, "Предупреждение", "Введите хост брокера")
            return

        from mqtt_client import MQTTClient
        temp_client = MQTTClient(host, port, username=username, password=password)

        if temp_client.connect():
            QMessageBox.information(self, "Успех", f"Подключен к {host}:{port}")
            self.log_text.append(f"✅ MQTT подключен к {host}:{port}")
            temp_client.disconnect()
        else:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к {host}:{port}")
            self.log_text.append(f"❌ Ошибка подключения к MQTT")

        temp_client.close()

    def test_server_connection(self):
        """Проверка соединения и авторизации"""
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

    def add_user(self):
        """Добавление пользователя на VDS сервер"""
        chat_id = self.new_user_input.text().strip()
        if not chat_id:
            QMessageBox.warning(self, "Предупреждение", "Введите chat_id")
            return

        for i in range(self.users_list.count()):
            if self.users_list.item(i).text() == chat_id:
                QMessageBox.warning(self, "Предупреждение", "Пользователь уже добавлен")
                return

        url = self.server_url_input.text().strip()
        api_key = self.api_key_input.text().strip()

        if not url:
            QMessageBox.warning(self, "Предупреждение", "Введите URL сервера")
            return

        temp_client = ServerClient(url, api_key)
        response = temp_client.add_user(chat_id)
        temp_client.close()

        if response.get('success'):
            self.users_list.addItem(chat_id)
            self.new_user_input.clear()
            self.log_text.append(f"✅ Пользователь {chat_id} добавлен")
        else:
            error = response.get('message', 'Неизвестная ошибка')
            self.log_text.append(f"❌ Ошибка: {error}")
            QMessageBox.critical(self, "Ошибка", error)

    def remove_user(self):
        """Удаление пользователя с VDS сервера"""
        selected = self.users_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Предупреждение", "Выберите пользователя")
            return

        chat_id = selected[0].text()

        url = self.server_url_input.text().strip()
        api_key = self.api_key_input.text().strip()

        temp_client = ServerClient(url, api_key)
        response = temp_client.delete_user(chat_id)
        temp_client.close()

        if response.get('success'):
            self.users_list.takeItem(self.users_list.row(selected[0]))
            self.log_text.append(f"🗑️ Пользователь {chat_id} удален")
        else:
            error = response.get('message', 'Неизвестная ошибка')
            self.log_text.append(f"❌ Ошибка: {error}")

    def load_users(self):
        """Загрузка списка пользователей с VDS сервера"""
        url = self.server_url_input.text().strip()
        api_key = self.api_key_input.text().strip()

        if not url:
            return

        temp_client = ServerClient(url, api_key)
        users = temp_client.get_users()
        temp_client.close()

        self.users_list.clear()
        for user in users:
            chat_id = user.get('chat_id', '')
            if chat_id:
                self.users_list.addItem(chat_id)

        self.log_text.append(f"🔄 Загружено пользователей: {self.users_list.count()}")

    def save_settings(self):
        """Сохранение настроек"""
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