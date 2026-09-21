from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QTableWidget, QTableWidgetItem, QPushButton,
                               QLabel, QHeaderView, QFrame, QAbstractItemView,
                               QComboBox, QDateEdit, QMessageBox, QMenu)
from PySide6.QtCore import Qt, Signal, QDateTime, QDate
from PySide6.QtGui import QColor, QFont
from datetime import datetime


class AuditTab(QWidget):
    """Вкладка аудита действий"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.audit_records = []
        self.filtered_records = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок
        header = QLabel("🔍 Аудит действий")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2196F3;
            padding: 5px;
            background-color: transparent;
        """)
        layout.addWidget(header)

        # Панель фильтров
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #d5d8dc;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        # Фильтр по типу действия
        filter_layout.addWidget(QLabel("Тип действия:"))
        self.action_type_combo = QComboBox()
        self.action_type_combo.addItem("Все", None)
        self.action_type_combo.addItem("Сохранение результата", "save_result")
        self.action_type_combo.addItem("Пакетное сохранение", "save_results_batch")
        self.action_type_combo.addItem("Игнорирование", "ignored")
        self.action_type_combo.addItem("Снятие игнорирования", "unignored")
        self.action_type_combo.addItem("Пакетное игнорирование", "batch_ignore")
        self.action_type_combo.addItem("Подключение к БД", "db_connect")
        self.action_type_combo.addItem("Отключение от БД", "db_disconnect")
        self.action_type_combo.addItem("Запуск проверки", "check_start")
        self.action_type_combo.addItem("Завершение проверки", "check_finish")
        self.action_type_combo.addItem("Отправка в Telegram", "telegram_send")
        self.action_type_combo.addItem("Подтверждение из Telegram", "telegram_accept")
        self.action_type_combo.addItem("Применение настроек", "settings_apply")
        self.action_type_combo.addItem("Ошибка", "error")
        self.action_type_combo.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 11px;
                min-height: 25px;
            }
        """)
        filter_layout.addWidget(self.action_type_combo)

        # Фильтр по дате
        filter_layout.addWidget(QLabel("С:"))
        self.date_from_edit = QDateEdit()
        self.date_from_edit.setCalendarPopup(True)
        self.date_from_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_from_edit.setDate(QDate.currentDate().addDays(-7))
        self.date_from_edit.setStyleSheet("""
            QDateEdit {
                padding: 5px 10px;
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 11px;
                min-height: 25px;
            }
        """)
        filter_layout.addWidget(self.date_from_edit)

        filter_layout.addWidget(QLabel("По:"))
        self.date_to_edit = QDateEdit()
        self.date_to_edit.setCalendarPopup(True)
        self.date_to_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_to_edit.setDate(QDate.currentDate())
        self.date_to_edit.setStyleSheet("""
            QDateEdit {
                padding: 5px 10px;
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 11px;
                min-height: 25px;
            }
        """)
        filter_layout.addWidget(self.date_to_edit)

        # Кнопки
        self.apply_filter_btn = QPushButton("🔍 Применить")
        self.apply_filter_btn.clicked.connect(self.apply_filters)
        self.apply_filter_btn.setStyleSheet("""
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
        """)
        filter_layout.addWidget(self.apply_filter_btn)

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet("""
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
        filter_layout.addWidget(self.refresh_btn)

        filter_layout.addStretch()

        filter_frame.setLayout(filter_layout)
        layout.addWidget(filter_frame)

        # Статистика
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f5e9;
                border: 1px solid #a5d6a7;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)

        self.total_label = QLabel("Всего записей: 0")
        self.total_label.setStyleSheet("""
            color: #1565c0;
            font-weight: bold;
            font-size: 12px;
            background-color: transparent;
        """)

        self.shown_label = QLabel("Показано: 0")
        self.shown_label.setStyleSheet("""
            color: #2e7d32;
            font-weight: bold;
            font-size: 12px;
            background-color: transparent;
        """)

        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.shown_label)
        stats_layout.addStretch()

        # Кнопка очистки аудита
        self.clear_audit_btn = QPushButton("🗑️ Очистить аудит")
        self.clear_audit_btn.clicked.connect(self.clear_audit)
        self.clear_audit_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
                padding: 5px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        stats_layout.addWidget(self.clear_audit_btn)

        stats_frame.setLayout(stats_layout)
        layout.addWidget(stats_frame)

        # Таблица аудита
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Время", "Пользователь", "Действие", "Описание",
            "Объект", "ID объекта", "Детали"
        ])

        # Настройка таблицы
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)

        # Настройка заголовков
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultAlignment(Qt.AlignCenter)

        # Устанавливаем ширину колонок
        self.table.setColumnWidth(0, 150)  # Время
        self.table.setColumnWidth(1, 100)  # Пользователь
        self.table.setColumnWidth(2, 150)  # Действие
        self.table.setColumnWidth(3, 200)  # Описание
        self.table.setColumnWidth(4, 100)  # Объект
        self.table.setColumnWidth(5, 80)  # ID объекта
        self.table.setColumnWidth(6, 250)  # Детали

        self.table.setStyleSheet("""
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

        # Контекстное меню
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table)

        self.setLayout(layout)

    def refresh_data(self):
        """Обновление данных аудита"""
        if not self.main_window.db_manager.is_connected():
            return

        self.audit_records = self.main_window.db_manager.get_audit_log(limit=5000)
        self.apply_filters()

        # Обновляем статистику
        stats = self.main_window.db_manager.get_audit_statistics()
        self.total_label.setText(f"Всего записей: {stats['total']}")

    def apply_filters(self):
        """Применение фильтров"""
        action_type = self.action_type_combo.currentData()
        date_from = self.date_from_edit.date().toPython()
        date_to = self.date_to_edit.date().toPython()

        # Нормализуем границы в один формат
        date_from_str = date_from.strftime("%Y-%m-%d 00:00:00")
        date_to_str = date_to.strftime("%Y-%m-%d 23:59:59")

        self.filtered_records = []

        for record in self.audit_records:
            timestamp = (record.get('timestamp') or '').strip()
            record_action_type = record.get('action_type', '')

            if action_type and record_action_type != action_type:
                continue

            # Если timestamp пустой — не отбрасываем запись, а показываем
            if timestamp:
                # Нормализуем: заменяем 'T' на пробел и обрезаем до секунд
                ts_norm = timestamp.replace('T', ' ')
                if '.' in ts_norm:
                    ts_norm = ts_norm.split('.')[0]
                # Убедимся, что формат YYYY-MM-DD HH:MM:SS (19 символов)
                if len(ts_norm) >= 19:
                    ts_norm = ts_norm[:19]
                # Если короче (например, только дата) — дополним
                if len(ts_norm) == 10:
                    ts_norm = ts_norm + " 00:00:00"
                if not (date_from_str <= ts_norm <= date_to_str):
                    continue

            self.filtered_records.append(record)

        self._populate_table(self.filtered_records)
        self.shown_label.setText(f"Показано: {len(self.filtered_records)}")

    def _populate_table(self, records: list):
        """Заполнение таблицы аудита"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(records))

        for row, record in enumerate(records):
            # Время
            timestamp = record.get('timestamp', '')
            time_text = self._format_timestamp(timestamp)
            time_item = QTableWidgetItem(time_text)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, time_item)

            # Пользователь
            user = record.get('user', 'system')
            user_item = QTableWidgetItem(user)
            user_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, user_item)

            # Действие
            action_type = record.get('action_type', '')
            action_text = self._get_action_text(action_type)
            action_item = QTableWidgetItem(action_text)
            action_item.setTextAlignment(Qt.AlignCenter)

            # Цвет действия
            if action_type in ['error', 'ignored', 'batch_ignore']:
                action_item.setForeground(QColor("#d32f2f"))
            elif action_type in ['save_result', 'save_results_batch', 'check_start']:
                action_item.setForeground(QColor("#1976d2"))
            elif action_type in ['telegram_send', 'telegram_accept']:
                action_item.setForeground(QColor("#9b59b6"))
            else:
                action_item.setForeground(QColor("#2c3e50"))

            self.table.setItem(row, 2, action_item)

            # Описание
            description = record.get('action_description', '')
            desc_item = QTableWidgetItem(description)
            self.table.setItem(row, 3, desc_item)

            # Объект
            object_type = record.get('object_type', '')
            obj_item = QTableWidgetItem(object_type)
            obj_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, obj_item)

            # ID объекта
            object_id = record.get('object_id', '')
            obj_id_item = QTableWidgetItem(str(object_id))
            obj_id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, obj_id_item)

            # Детали
            details = record.get('details', '')
            details_item = QTableWidgetItem(details)
            details_item.setToolTip(details)
            self.table.setItem(row, 6, details_item)

            # Высота строки
            self.table.setRowHeight(row, 40)

        self.table.setSortingEnabled(True)

    def _format_timestamp(self, timestamp: str) -> str:
        """Форматирование временной метки"""
        if not timestamp:
            return ""

        try:
            dt = QDateTime.fromString(timestamp, "yyyy-MM-dd hh:mm:ss")
            if dt.isValid():
                return dt.toString("dd.MM.yyyy hh:mm:ss")
        except:
            pass

        return timestamp

    def _get_action_text(self, action_type: str) -> str:
        """Получение текстового описания действия"""
        actions = {
            'save_result': 'Сохранение результата',
            'save_results_batch': 'Пакетное сохранение',
            'ignored': 'Игнорирование',
            'unignored': 'Снятие игнорирования',
            'batch_ignore': 'Пакетное игнорирование',
            'db_connect': 'Подключение к БД',
            'db_disconnect': 'Отключение от БД',
            'check_start': 'Запуск проверки',
            'check_finish': 'Завершение проверки',
            'telegram_send': 'Отправка в Telegram',
            'telegram_accept': 'Подтверждение из Telegram',
            'settings_apply': 'Применение настроек',
            'error': 'Ошибка'
        }
        return actions.get(action_type, action_type)

    def clear_audit(self):
        """Очистка журнала аудита"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы действительно хотите очистить весь журнал аудита?\nЭто действие нельзя отменить.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.main_window.db_manager.clear_audit_log():
                self.main_window.log_message("Журнал аудита очищен")
                self.refresh_data()
                QMessageBox.information(self, "Успех", "Журнал аудита очищен")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось очистить журнал аудита")

    def _show_context_menu(self, position):
        """Показать контекстное меню"""
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                color: #2c3e50;
                border: 1px solid #d5d8dc;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)

        refresh_action = menu.addAction("🔄 Обновить")
        menu.addSeparator()
        clear_action = menu.addAction("🗑️ Очистить аудит")

        action = menu.exec(self.table.mapToGlobal(position))

        if action == refresh_action:
            self.refresh_data()
        elif action == clear_action:
            self.clear_audit()