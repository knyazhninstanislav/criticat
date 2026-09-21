from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QTableWidget, QTableWidgetItem, QPushButton,
                               QLabel, QHeaderView, QFrame, QAbstractItemView,
                               QMessageBox, QTabWidget, QLineEdit, QFormLayout,
                               QGroupBox, QScrollArea, QGridLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont


class VdsAdminTab(QWidget):
    """Админ-вкладка для управления VDS-бэкендом"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.users = []
        self.statistics = {}
        self.init_ui()

    # ================= UI =================

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок
        header = QLabel("🖥️ VDS Админка")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2196F3;
            padding: 5px;
            background-color: transparent;
        """)
        layout.addWidget(header)

        # Статус подключения
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3e0;
                border: 1px solid #ff9800;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(8, 4, 8, 4)

        self.status_label = QLabel("⚠️ Нет подключения к VDS")
        self.status_label.setStyleSheet("""
            color: #e65100;
            font-weight: bold;
            font-size: 12px;
            background-color: transparent;
        """)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.refresh_all)
        self.refresh_btn.setMinimumHeight(28)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
                padding: 5px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        status_layout.addWidget(self.refresh_btn)

        self.status_frame.setLayout(status_layout)
        layout.addWidget(self.status_frame)

        # Внутренние табы: Пользователи / Статистика
        self.inner_tabs = QTabWidget()
        self.inner_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                color: #2c3e50;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                font-size: 11px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d5d8dc;
            }
        """)

        self.users_tab = self._build_users_tab()
        self.stats_tab = self._build_stats_tab()

        self.inner_tabs.addTab(self.users_tab, "👥 Пользователи")
        self.inner_tabs.addTab(self.stats_tab, "📊 Статистика")

        layout.addWidget(self.inner_tabs)

        self.setLayout(layout)

    # ================= Пользователи =================

    def _build_users_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Форма добавления
        add_group = QGroupBox("➕ Добавить / обновить пользователя")
        add_group.setStyleSheet("""
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

        form = QFormLayout()
        form.setSpacing(8)
        form.setContentsMargins(5, 5, 5, 5)

        input_style = """
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 12px;
                min-height: 22px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #f7f9fc;
            }
        """

        self.chat_id_input = QLineEdit()
        self.chat_id_input.setPlaceholderText("Например: 123456789")
        self.chat_id_input.setStyleSheet(input_style)
        form.addRow(QLabel("Chat ID *"), self.chat_id_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("@username")
        self.username_input.setStyleSheet(input_style)
        form.addRow(QLabel("Username"), self.username_input)

        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Иванов Иван Иванович")
        self.full_name_input.setStyleSheet(input_style)
        form.addRow(QLabel("ФИО"), self.full_name_input)

        self.department_input = QLineEdit()
        self.department_input.setPlaceholderText("Отделение")
        self.department_input.setStyleSheet(input_style)
        form.addRow(QLabel("Отделение"), self.department_input)

        # Строка с кнопками — создаём отдельный QWidget с QHBoxLayout
        btn_widget = QWidget()
        btn_row = QHBoxLayout(btn_widget)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(8)

        self.add_user_btn = QPushButton("💾 Добавить / обновить")
        self.add_user_btn.clicked.connect(self.add_or_update_user)
        self.add_user_btn.setMinimumHeight(35)
        self.add_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 8px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)

        self.clear_form_btn = QPushButton("✕ Очистить")
        self.clear_form_btn.clicked.connect(self._clear_user_form)
        self.clear_form_btn.setMinimumHeight(35)
        self.clear_form_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 8px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)

        btn_row.addWidget(self.add_user_btn)
        btn_row.addWidget(self.clear_form_btn)
        btn_row.addStretch()

        form.addRow("", btn_widget)

        add_group.setLayout(form)
        layout.addWidget(add_group)

        # Таблица пользователей
        users_group = QGroupBox("👥 Список пользователей")
        users_group.setStyleSheet(add_group.styleSheet())
        users_layout = QVBoxLayout()
        users_layout.setContentsMargins(5, 5, 5, 5)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels([
            "Chat ID", "Username", "ФИО", "Отделение", "Статус", "Действия"
        ])
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.users_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.verticalHeader().setVisible(False)

        header = self.users_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultAlignment(Qt.AlignCenter)

        self.users_table.setColumnWidth(0, 120)
        self.users_table.setColumnWidth(1, 140)
        self.users_table.setColumnWidth(2, 200)
        self.users_table.setColumnWidth(3, 160)
        self.users_table.setColumnWidth(4, 100)
        self.users_table.setColumnWidth(5, 180)

        self.users_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                background-color: #ffffff;
                gridline-color: #e0e0e0;
                font-size: 11px;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 5px;
                color: #2c3e50;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565c0;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-weight: bold;
                font-size: 11px;
                padding: 8px;
                border: 1px solid #d5d8dc;
                border-left: none;
                border-top: none;
            }
        """)

        users_layout.addWidget(self.users_table)
        users_group.setLayout(users_layout)
        layout.addWidget(users_group)

        widget.setLayout(layout)
        return widget

    # ================= Статистика =================

    def _build_stats_tab(self) -> QWidget:
        # Внешний контейнер с прокруткой
        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical {
                background-color: #f0f2f5;
                width: 10px;
                border-radius: 5px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background-color: #95a5a6; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # ==== Карточки ====
        self.stats_cards_frame = QFrame()
        self.stats_cards_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #d5d8dc;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.stats_cards_layout = QGridLayout()
        self.stats_cards_layout.setSpacing(10)
        self.stats_cards_layout.setContentsMargins(10, 10, 10, 10)

        self.stat_total_card = self._create_stat_card("Всего результатов", "0", "#2196F3")
        self.stat_pending_card = self._create_stat_card("В ожидании", "0", "#f39c12")
        self.stat_confirmed_card = self._create_stat_card("Подтверждено", "0", "#4caf50")
        self.stat_rejected_card = self._create_stat_card("Отклонено", "0", "#e74c3c")
        self.stat_users_card = self._create_stat_card("Активных пользователей", "0", "#9b59b6")
        self.stat_today_card = self._create_stat_card("Сегодня", "0", "#16a085")

        self.stats_cards_layout.addWidget(self.stat_total_card, 0, 0)
        self.stats_cards_layout.addWidget(self.stat_pending_card, 0, 1)
        self.stats_cards_layout.addWidget(self.stat_confirmed_card, 0, 2)
        self.stats_cards_layout.addWidget(self.stat_rejected_card, 1, 0)
        self.stats_cards_layout.addWidget(self.stat_users_card, 1, 1)
        self.stats_cards_layout.addWidget(self.stat_today_card, 1, 2)

        self.stats_cards_frame.setLayout(self.stats_cards_layout)
        layout.addWidget(self.stats_cards_frame)
        layout.addStretch()

        scroll.setWidget(inner)
        outer_layout.addWidget(scroll)
        return outer

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("stat_card")
        card.setStyleSheet(f"""
            QFrame#stat_card {{
                background-color: #ffffff;
                border: 2px solid {color};
                border-radius: 8px;
            }}
        """)
        card.setMinimumHeight(90)
        card.setMinimumWidth(160)

        v = QVBoxLayout(card)
        v.setSpacing(4)
        v.setContentsMargins(12, 12, 12, 12)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("title_label")
        title_lbl.setStyleSheet(f"""
            color: {color};
            font-size: 11px;
            font-weight: bold;
            background-color: transparent;
            border: none;
        """)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setWordWrap(True)

        value_lbl = QLabel(value)
        value_lbl.setObjectName("value_label")
        value_lbl.setStyleSheet(f"""
            color: {color};
            font-size: 22px;
            font-weight: bold;
            background-color: transparent;
            border: none;
        """)
        value_lbl.setAlignment(Qt.AlignCenter)

        v.addWidget(title_lbl)
        v.addWidget(value_lbl)

        # ПРЯМАЯ ссылка — гарантированно работает
        card._value_label = value_lbl
        return card

    def _set_card_value(self, card: QFrame, value: str):
        # Сначала пробуем прямую ссылку (надёжно)
        lbl = getattr(card, "_value_label", None)
        if lbl is None:
            # fallback — по objectName
            lbl = card.findChild(QLabel, "value_label")
        if lbl is not None:
            lbl.setText(str(value))
        else:
            self.main_window.log_message(f"⚠️ Не найден value_label в карточке {card}")

    def _set_card_value(self, card: QFrame, value: str):
        lbl = getattr(card, "_value_label", None)
        if lbl is not None:
            lbl.setText(str(value))
        else:
            # fallback — старый способ
            lbl = card.findChild(QLabel, "value_label")
            if lbl:
                lbl.setText(str(value))

    # ================= Логика =================

    def set_connected(self, connected: bool, message: str = ""):
        """Обновление статуса подключения"""
        if connected:
            self.status_frame.setStyleSheet("""
                QFrame {
                    background-color: #e8f5e9;
                    border: 1px solid #a5d6a7;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
            self.status_label.setText(f"✅ Подключено к VDS{(' — ' + message) if message else ''}")
            self.status_label.setStyleSheet("""
                color: #2e7d32;
                font-weight: bold;
                font-size: 12px;
                background-color: transparent;
            """)
            self.refresh_btn.setEnabled(True)
            self.inner_tabs.setEnabled(True)
        else:
            self.status_frame.setStyleSheet("""
                QFrame {
                    background-color: #ffebee;
                    border: 1px solid #ef9a9a;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
            self.status_label.setText(f"❌ Нет подключения к VDS{(' — ' + message) if message else ''}")
            self.status_label.setStyleSheet("""
                color: #c62828;
                font-weight: bold;
                font-size: 12px;
                background-color: transparent;
            """)
            self.refresh_btn.setEnabled(False)
            self.inner_tabs.setEnabled(False)

    def refresh_all(self):
        """Обновление данных с сервера"""
        if not self.main_window.server_client.is_configured():
            self.set_connected(False, "Не настроен")
            return

        ok, msg = self.main_window.server_client.verify_auth()
        self.set_connected(ok, msg)

        if not ok:
            self.main_window.log_audit(
                "vds_error", "Ошибка авторизации VDS", "server", "",
                f"message={msg}"
            )
            return

        self.main_window.log_audit(
            "vds_refresh", "Обновление данных VDS-админки", "server", "", ""
        )

        self.load_users()
        self.load_statistics()

    # ---------- Пользователи ----------


    def load_users(self):
        """Загрузка списка пользователей"""
        try:
            users = self.main_window.server_client.get_users()
            self.users = users if isinstance(users, list) else []
            self._populate_users_table()
            self.main_window.log_audit(
                "vds_users_load", "Загрузка списка пользователей VDS",
                "server", "", f"count={len(self.users)}"
            )
        except Exception as e:
            self.main_window.log_message(f"❌ Ошибка загрузки пользователей: {e}")
            self.main_window.log_audit(
                "vds_error", "Ошибка загрузки пользователей VDS",
                "server", "", str(e)
            )
    def _populate_users_table(self):
        self.users_table.setRowCount(len(self.users))

        for row, user in enumerate(self.users):
            chat_id = str(user.get('chat_id', ''))
            username = user.get('username', '') or '—'
            full_name = user.get('full_name', '') or '—'
            department = user.get('department', '') or '—'
            is_active = user.get('is_active', False)

            # Chat ID
            item = QTableWidgetItem(chat_id)
            item.setTextAlignment(Qt.AlignCenter)
            item.setData(Qt.UserRole, user)
            self.users_table.setItem(row, 0, item)

            # Username
            self.users_table.setItem(row, 1, QTableWidgetItem(username))

            # ФИО
            self.users_table.setItem(row, 2, QTableWidgetItem(full_name))

            # Отделение
            dept_item = QTableWidgetItem(department)
            dept_item.setForeground(QColor("#1565c0"))
            self.users_table.setItem(row, 3, dept_item)

            # Статус
            if is_active:
                status_item = QTableWidgetItem("✓ Активен")
                status_item.setForeground(QColor("#2e7d32"))
            else:
                status_item = QTableWidgetItem("🚫 Отключен")
                status_item.setForeground(QColor("#c62828"))
            status_item.setTextAlignment(Qt.AlignCenter)
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)
            self.users_table.setItem(row, 4, status_item)

            # Кнопки действий
            # Кнопки действий
            actions_widget = QWidget()
            actions_widget.setStyleSheet("background-color: transparent;")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(6)
            actions_layout.setAlignment(Qt.AlignCenter)

            btn_style_common = """
                QPushButton {
                    border: none;
                    border-radius: 3px;
                    font-size: 13px;
                    color: white;
                    padding: 0px;
                }
            """

            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Загрузить в форму для редактирования")
            edit_btn.setFixedSize(30, 26)
            edit_btn.setStyleSheet(btn_style_common + """
                QPushButton { background-color: #3498db; }
                QPushButton:hover { background-color: #2980b9; }
            """)
            edit_btn.clicked.connect(lambda _, u=user: self._load_user_to_form(u))
            actions_layout.addWidget(edit_btn)

            if is_active:
                toggle_btn = QPushButton("🚫")
                toggle_btn.setToolTip("Деактивировать")
                toggle_btn.setStyleSheet(btn_style_common + """
                    QPushButton { background-color: #e74c3c; }
                    QPushButton:hover { background-color: #c0392b; }
                """)
            else:
                toggle_btn = QPushButton("✓")
                toggle_btn.setToolTip("Активировать")
                toggle_btn.setStyleSheet(btn_style_common + """
                    QPushButton { background-color: #27ae60; }
                    QPushButton:hover { background-color: #229954; }
                """)
            toggle_btn.setFixedSize(30, 26)
            toggle_btn.clicked.connect(lambda _, u=user: self._toggle_user_active(u))
            actions_layout.addWidget(toggle_btn)

            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("Удалить пользователя")
            delete_btn.setFixedSize(30, 26)
            delete_btn.setStyleSheet(btn_style_common + """
                QPushButton { background-color: #7f8c8d; }
                QPushButton:hover { background-color: #5a6c7d; }
            """)
            delete_btn.clicked.connect(lambda _, cid=chat_id: self._delete_user(cid))
            actions_layout.addWidget(delete_btn)

            actions_layout.addStretch()
            actions_widget.setLayout(actions_layout)
            self.users_table.setCellWidget(row, 5, actions_widget)

            self.users_table.setRowHeight(row, 44)

    def _load_user_to_form(self, user: dict):
        """Загрузка пользователя в форму"""
        self.chat_id_input.setText(str(user.get('chat_id', '')))
        self.username_input.setText(user.get('username', '') or '')
        self.full_name_input.setText(user.get('full_name', '') or '')
        self.department_input.setText(user.get('department', '') or '')
        self.chat_id_input.setFocus()

    def _clear_user_form(self):
        self.chat_id_input.clear()
        self.username_input.clear()
        self.full_name_input.clear()
        self.department_input.clear()


    def add_or_update_user(self):
        """Добавление или обновление пользователя"""
        if not self.main_window.server_client.is_configured():
            QMessageBox.warning(self, "Ошибка", "Нет подключения к VDS")
            return

        chat_id = self.chat_id_input.text().strip()
        if not chat_id:
            QMessageBox.warning(self, "Предупреждение", "Введите Chat ID")
            return

        payload = {
            'chat_id': chat_id,
            'username': self.username_input.text().strip(),
            'full_name': self.full_name_input.text().strip(),
            'department': self.department_input.text().strip(),
        }

        response = self.main_window.server_client.add_user_full(payload)

        if response.get('success'):
            self.main_window.log_message(f"✅ Пользователь {chat_id} сохранён")
            self.main_window.log_audit(
                "vds_user_save", "Добавление/обновление пользователя VDS",
                "server_user", chat_id,
                f"username={payload['username']}, "
                f"full_name={payload['full_name']}, "
                f"department={payload['department']}"
            )
            self._clear_user_form()
            self.load_users()
            QMessageBox.information(self, "Успех", "Пользователь сохранён")
        else:
            err = response.get('message', 'Неизвестная ошибка')
            self.main_window.log_message(f"❌ Ошибка: {err}")
            self.main_window.log_audit(
                "vds_error", "Ошибка сохранения пользователя VDS",
                "server_user", chat_id, err
            )
            QMessageBox.critical(self, "Ошибка", err)


    def _toggle_user_active(self, user: dict):
        """Переключение активности пользователя"""
        chat_id = str(user.get('chat_id', ''))
        is_active = user.get('is_active', False)

        if is_active:
            response = self.main_window.server_client.delete_user(chat_id)
            action = "деактивирован"
            audit_action = "vds_user_deactivate"
            audit_desc = "Деактивация пользователя VDS"
        else:
            payload = {
                'chat_id': chat_id,
                'username': user.get('username', ''),
                'full_name': user.get('full_name', ''),
                'department': user.get('department', ''),
            }
            response = self.main_window.server_client.add_user_full(payload)
            action = "активирован"
            audit_action = "vds_user_activate"
            audit_desc = "Активация пользователя VDS"

        if response.get('success'):
            self.main_window.log_message(f"✅ Пользователь {chat_id} {action}")
            self.main_window.log_audit(
                audit_action, audit_desc, "server_user", chat_id, ""
            )
            self.load_users()
        else:
            err = response.get('message', 'Неизвестная ошибка')
            self.main_window.log_audit(
                "vds_error", f"Ошибка ({action}) пользователя VDS",
                "server_user", chat_id, err
            )
            QMessageBox.critical(self, "Ошибка", err)


    def _delete_user(self, chat_id: str):
        """Удаление (деактивация) пользователя с подтверждением"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить пользователя {chat_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        response = self.main_window.server_client.delete_user(chat_id)
        if response.get('success'):
            self.main_window.log_message(f"🗑️ Пользователь {chat_id} удалён")
            self.main_window.log_audit(
                "vds_user_delete", "Удаление пользователя VDS",
                "server_user", chat_id, ""
            )
            self.load_users()
        else:
            err = response.get('message', 'Неизвестная ошибка')
            self.main_window.log_audit(
                "vds_error", "Ошибка удаления пользователя VDS",
                "server_user", chat_id, err
            )
            QMessageBox.critical(self, "Ошибка", err)

    # ---------- Статистика ----------


    def load_statistics(self):
        """Загрузка статистики"""
        try:
            stats = self.main_window.server_client.get_statistics()
            if not isinstance(stats, dict):
                stats = {}
            self.statistics = stats
            self._update_statistics_ui(stats)
            self.main_window.log_audit(
                "vds_stats_load", "Загрузка статистики VDS",
                "server", "", f"keys={list(stats.keys())}"
            )
        except Exception as e:
            self.main_window.log_message(f"❌ Ошибка загрузки статистики: {e}")
            self.main_window.log_audit(
                "vds_error", "Ошибка загрузки статистики VDS",
                "server", "", str(e)
            )

    def _update_statistics_ui(self, stats: dict):
        """Обновление UI статистики с поддержкой вложенной структуры"""
        if not isinstance(stats, dict):
            stats = {}

        # ---------- Плоское представление ----------
        def flatten(d, prefix=''):
            out = {}
            for k, v in d.items():
                key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
                if isinstance(v, dict):
                    out.update(flatten(v, prefix=key))
                else:
                    out[key] = v
            return out

        flat = flatten(stats)

        # Отладка — по желанию можно убрать
        self.main_window.log_message(f"📊 VDS stats flat: {flat}")

        # ---------- Хелпер: найти значение по ключу ----------
        def pick(*keys, default=0):
            """Ищет значение по ключам: точное совпадение, затем по окончанию."""
            for k in keys:
                if k in flat:
                    return flat[k]
            for k in keys:
                for fk, fv in flat.items():
                    if fk == k or fk.endswith('.' + k):
                        return fv
            return default

        # ---------- Маппинг на 6 карточек ----------
        # ВАЖНО: для total/pending/confirmed/rejected указываем ветку results,
        # чтобы не поймать одноимённые ключи из users.
        total        = pick('results.total', 'total')
        pending      = pick('results.pending', 'pending', 'in_progress')
        confirmed    = pick('results.confirmed', 'confirmed')
        rejected     = pick('results.rejected', 'rejected')
        active_users = pick('users.active', 'active_users', 'active')
        today        = pick('results.today', 'today', 'created_today')

        self._set_card_value(self.stat_total_card, total)
        self._set_card_value(self.stat_pending_card, pending)
        self._set_card_value(self.stat_confirmed_card, confirmed)
        self._set_card_value(self.stat_rejected_card, rejected)
        self._set_card_value(self.stat_users_card, active_users)
        self._set_card_value(self.stat_today_card, today)

        # ---------- Детальная таблица (плоские ключи) ----------
        flat_items = list(flat.items())

        self.stats_detail_table.setRowCount(len(flat_items))
        for row, (key, value) in enumerate(flat_items):
            key_item = QTableWidgetItem(str(key))
            key_item.setForeground(QColor("#2c3e50"))
            f = key_item.font()
            f.setBold(True)
            key_item.setFont(f)

            val_item = QTableWidgetItem(str(value))
            val_item.setForeground(QColor("#1565c0"))

            self.stats_detail_table.setItem(row, 0, key_item)
            self.stats_detail_table.setItem(row, 1, val_item)
            self.stats_detail_table.setRowHeight(row, 32)