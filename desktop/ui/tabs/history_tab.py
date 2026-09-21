from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QTableWidget, QTableWidgetItem, QPushButton,
                               QLabel, QHeaderView, QFrame, QAbstractItemView,
                               QMessageBox, QMenu, QButtonGroup)
from PySide6.QtCore import Qt, Signal, QDateTime
from PySide6.QtGui import QColor, QFont
from ui.widgets.search_widget import SearchWidget
from datetime import datetime


class HistoryTab(QWidget):
    ignore_toggled = Signal(int, bool)  # result_id, is_ignored

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.all_results = []
        self.filtered_results = []
        self.current_filter = 'all'
        self.current_search = None
        self.current_date_filter = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок
        header = QLabel("📋 История критических результатов")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2196F3;
            padding: 5px;
            background-color: transparent;
        """)
        layout.addWidget(header)

        # Поиск с фильтром дат
        self.search_widget = SearchWidget()
        self.search_widget.search_requested.connect(self._on_search)
        self.search_widget.search_cleared.connect(self._on_search_cleared)
        self.search_widget.date_filter_changed.connect(self._on_date_filter_changed)
        layout.addWidget(self.search_widget)

        # Панель управления с фильтрами
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #d5d8dc;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        # Фильтры
        filters_label = QLabel("Показать:")
        filters_label.setStyleSheet("""
            color: #2c3e50;
            font-weight: bold;
            font-size: 12px;
            background-color: transparent;
        """)

        # Создаем группу кнопок для фильтров
        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)

        self.show_all_btn = QPushButton("Все")
        self.show_all_btn.setCheckable(True)
        self.show_all_btn.setChecked(True)
        self.show_all_btn.clicked.connect(lambda: self._set_filter('all'))

        self.show_active_btn = QPushButton("Активные")
        self.show_active_btn.setCheckable(True)
        self.show_active_btn.clicked.connect(lambda: self._set_filter('active'))

        self.show_ignored_btn = QPushButton("Игнорируемые")
        self.show_ignored_btn.setCheckable(True)
        self.show_ignored_btn.clicked.connect(lambda: self._set_filter('ignored'))

        self.filter_group.addButton(self.show_all_btn)
        self.filter_group.addButton(self.show_active_btn)
        self.filter_group.addButton(self.show_ignored_btn)

        # Стили для кнопок фильтров
        filter_style = """
            QPushButton {
                color: white;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
                padding: 5px 15px;
                border: none;
                min-height: 25px;
            }
            QPushButton:checked {
                border: 2px solid #2c3e50;
            }
        """

        self.show_all_btn.setStyleSheet(filter_style + """
            QPushButton {
                background-color: #3498db;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        self.show_active_btn.setStyleSheet(filter_style + """
            QPushButton {
                background-color: #4caf50;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)

        self.show_ignored_btn.setStyleSheet(filter_style + """
            QPushButton {
                background-color: #f57c00;
            }
            QPushButton:hover {
                background-color: #e65100;
            }
        """)

        control_layout.addWidget(filters_label)
        control_layout.addWidget(self.show_all_btn)
        control_layout.addWidget(self.show_active_btn)
        control_layout.addWidget(self.show_ignored_btn)
        control_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setMinimumHeight(30)
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
        """)
        control_layout.addWidget(self.refresh_btn)

        control_frame.setLayout(control_layout)
        layout.addWidget(control_frame)

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

        self.total_label = QLabel("Всего: 0")
        self.total_label.setStyleSheet("""
            color: #1565c0;
            font-weight: bold;
            font-size: 12px;
            background-color: transparent;
        """)

        self.active_label = QLabel("Активных: 0")
        self.active_label.setStyleSheet("""
            color: #2e7d32;
            font-weight: bold;
            font-size: 12px;
            background-color: transparent;
        """)

        self.ignored_label = QLabel("Игнорируется: 0")
        self.ignored_label.setStyleSheet("""
            color: #e65100;
            font-weight: bold;
            font-size: 12px;
            background-color: transparent;
        """)

        self.filtered_label = QLabel("Показано: 0")
        self.filtered_label.setStyleSheet("""
            color: #7f8c8d;
            font-weight: bold;
            font-size: 12px;
            background-color: transparent;
        """)

        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.active_label)
        stats_layout.addWidget(self.ignored_label)
        stats_layout.addWidget(self.filtered_label)
        stats_layout.addStretch()

        stats_frame.setLayout(stats_layout)
        layout.addWidget(stats_frame)

        # Таблица результатов
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Пациент", "Отделение", "Тест", "Значение",
            "Отклонение", "Дата обнаружения", "Статус", "Действия"
        ])

        # Настройка таблицы
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
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
        self.table.setColumnWidth(0, 60)  # ID
        self.table.setColumnWidth(1, 200)  # Пациент
        self.table.setColumnWidth(2, 150)  # Отделение
        self.table.setColumnWidth(3, 130)  # Тест
        self.table.setColumnWidth(4, 90)  # Значение
        self.table.setColumnWidth(5, 90)  # Отклонение
        self.table.setColumnWidth(6, 150)  # Дата обнаружения
        self.table.setColumnWidth(7, 120)  # Статус
        self.table.setColumnWidth(8, 100)  # Действия

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
            QTableCornerButton::section {
                background-color: #f8f9fa;
                border: 1px solid #d5d8dc;
            }
        """)

        # Подключаем контекстное меню
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Подключаем двойной клик
        self.table.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)

        # Кнопки действий
        action_frame = QFrame()
        action_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)

        self.toggle_ignore_btn = QPushButton("🔄 Сменить статус выбранных")
        self.toggle_ignore_btn.clicked.connect(self._toggle_selected_ignore)
        self.toggle_ignore_btn.setMinimumHeight(35)
        self.toggle_ignore_btn.setEnabled(False)
        self.toggle_ignore_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 8px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)

        self.ignore_all_visible_btn = QPushButton("🚫 Игнорировать все активные")
        self.ignore_all_visible_btn.clicked.connect(self._ignore_all_visible)
        self.ignore_all_visible_btn.setMinimumHeight(35)
        self.ignore_all_visible_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 8px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        action_layout.addWidget(self.toggle_ignore_btn)
        action_layout.addWidget(self.ignore_all_visible_btn)
        action_layout.addStretch()

        action_frame.setLayout(action_layout)
        layout.addWidget(action_frame)

        # Подключаем выбор строки
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        self.setLayout(layout)

    def _on_search(self, search_params: dict):
        """Обработчик поиска"""
        self.current_search = search_params
        self._apply_filters_and_search()

    def _on_search_cleared(self):
        """Обработчик очистки поиска"""
        self.current_search = None
        self._apply_filters_and_search()

    def _on_date_filter_changed(self, date_filter):
        """Обработчик изменения фильтра дат"""
        self.current_date_filter = date_filter
        self._apply_filters_and_search()

    def _apply_filters_and_search(self):
        """Применение фильтров, поиска и диапазона дат"""
        # Применяем фильтр статуса
        if self.current_filter == 'all':
            filtered = self.all_results
        elif self.current_filter == 'active':
            filtered = [r for r in self.all_results if not r.get('is_ignored', 0)]
        elif self.current_filter == 'ignored':
            filtered = [r for r in self.all_results if r.get('is_ignored', 0)]
        else:
            filtered = self.all_results

        # Применяем фильтр по датам
        if self.current_date_filter:
            date_from = self.current_date_filter.get('date_from')
            date_to = self.current_date_filter.get('date_to')

            if date_from and date_to:
                # Преобразуем в datetime для сравнения
                date_from_dt = datetime.combine(date_from, datetime.min.time())
                date_to_dt = datetime.combine(date_to, datetime.max.time())

                date_filtered = []
                for item in filtered:
                    found_at = item.get('found_at', '')
                    if found_at:
                        try:
                            # Пробуем разные форматы дат
                            item_date = None
                            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                                try:
                                    item_date = datetime.strptime(found_at, fmt)
                                    break
                                except ValueError:
                                    continue

                            if item_date and date_from_dt <= item_date <= date_to_dt:
                                date_filtered.append(item)
                        except:
                            # Если не удалось распарсить дату, включаем элемент
                            date_filtered.append(item)
                    else:
                        # Если нет даты, включаем элемент
                        date_filtered.append(item)

                filtered = date_filtered

        # Применяем поиск
        if self.current_search:
            search_text = self.current_search['text']
            search_type = self.current_search['type']
            case_sensitive = self.current_search['case_sensitive']
            exact_match = self.current_search['exact_match']

            if not case_sensitive:
                search_text = search_text.lower()

            search_results = []

            for item in filtered:
                if search_type == 'all':
                    fields_to_search = ['full_name', 'ids', 'department', 'test_name']
                else:
                    fields_to_search = [search_type]

                match_found = False

                for field in fields_to_search:
                    field_value = str(item.get(field, ''))

                    if not case_sensitive:
                        field_value = field_value.lower()

                    if exact_match:
                        if field_value == search_text:
                            match_found = True
                            break
                    else:
                        if search_text in field_value:
                            match_found = True
                            break

                if match_found:
                    search_results.append(item)

            self.filtered_results = search_results
        else:
            self.filtered_results = filtered

        # Обновляем таблицу
        self._populate_table(self.filtered_results)

        # Обновляем счетчики
        self.filtered_label.setText(f"Показано: {len(self.filtered_results)}")
        self.search_widget.set_results_count(len(self.filtered_results))

    def _set_filter(self, filter_type: str):
        """Установка фильтра отображения"""
        self.current_filter = filter_type
        self._apply_filters_and_search()

    def refresh_data(self):
        """Обновление данных из БД"""
        if not self.main_window.db_manager.is_connected():
            return

        # Получаем все результаты
        self.all_results = self.main_window.db_manager.get_all_critical_results(
            show_ignored=True,
            show_active=True
        )

        # Применяем фильтры и поиск
        self._apply_filters_and_search()

        # Обновляем статистику
        stats = self.main_window.db_manager.get_statistics()
        self.total_label.setText(f"Всего: {stats['total']}")
        self.active_label.setText(f"Активных: {stats['active']}")
        self.ignored_label.setText(f"Игнорируется: {stats['ignored']}")

    def _populate_table(self, results: list):
        """Заполнение таблицы данными"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(results))

        for row, result in enumerate(results):
            # ID
            id_item = QTableWidgetItem(str(result.get('result_id', '')))
            id_item.setTextAlignment(Qt.AlignCenter)
            id_item.setData(Qt.UserRole, result.get('result_id'))
            self.table.setItem(row, 0, id_item)

            # Пациент (ФИО + IDS)
            full_name = result.get('full_name', '')
            ids = result.get('ids', '')
            patient_text = f"{full_name}\n(IDS: {ids})"
            patient_item = QTableWidgetItem(patient_text)
            patient_item.setToolTip(f"{full_name}\nIDS: {ids}")
            self.table.setItem(row, 1, patient_item)

            # Отделение
            department = result.get('department', 'Не указано')
            dept_item = QTableWidgetItem(department)
            dept_item.setForeground(QColor("#1565c0"))
            dept_item.setToolTip(department)
            self.table.setItem(row, 2, dept_item)

            # Тест
            test_name = result.get('test_name', '')
            test_item = QTableWidgetItem(test_name)
            self.table.setItem(row, 3, test_item)

            # Значение
            value = result.get('result_value', 0)
            ref_lower = result.get('ref_lower', 0)
            ref_upper = result.get('ref_upper', 0)

            value_text = f"{value:.2f}"
            value_item = QTableWidgetItem(value_text)
            value_item.setTextAlignment(Qt.AlignCenter)
            value_item.setForeground(QColor("#d32f2f"))
            font = value_item.font()
            font.setBold(True)
            value_item.setFont(font)
            value_item.setToolTip(f"Норма: {ref_lower:.2f} - {ref_upper:.2f}")
            self.table.setItem(row, 4, value_item)

            # Отклонение
            deviation = result.get('deviation_percent', 0)
            if value > ref_upper:
                deviation_text = f"⬆️ +{deviation:.1f}%"
            else:
                deviation_text = f"⬇️ -{deviation:.1f}%"

            deviation_item = QTableWidgetItem(deviation_text)
            deviation_item.setTextAlignment(Qt.AlignCenter)
            deviation_item.setForeground(QColor("#d32f2f"))
            font = deviation_item.font()
            font.setBold(True)
            deviation_item.setFont(font)
            self.table.setItem(row, 5, deviation_item)

            # Дата обнаружения
            found_at = result.get('found_at', '')
            date_text = self._format_date(found_at)
            date_item = QTableWidgetItem(date_text)
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setToolTip(f"Обнаружено: {date_text}")
            self.table.setItem(row, 6, date_item)

            # Статус
            is_ignored = result.get('is_ignored', 0)
            ignored_at = result.get('ignored_at', '')

            if is_ignored:
                status_text = "🚫 Игнорируется"
                status_color = QColor("#f57c00")
                if ignored_at:
                    status_text += f"\n{self._format_date(ignored_at)}"
            else:
                status_text = "✓ Активен"
                status_color = QColor("#4caf50")

            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(status_color)
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)
            status_item.setToolTip(status_text.replace('\n', ' '))
            self.table.setItem(row, 7, status_item)

            # Кнопка действия
            action_btn = QPushButton("Переключить" if is_ignored else "Игнорировать")
            action_btn.setProperty('result_id', result.get('result_id'))
            action_btn.setProperty('is_ignored', is_ignored)
            action_btn.clicked.connect(self._on_action_clicked)
            action_btn.setMinimumHeight(25)
            action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    font-weight: bold;
                    font-size: 10px;
                    border-radius: 3px;
                    padding: 3px 8px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #e67e22;
                }
            """)
            self.table.setCellWidget(row, 8, action_btn)

            # Устанавливаем высоту строки
            self.table.setRowHeight(row, 50)

            # Фон строки в зависимости от статуса
            if is_ignored:
                for col in range(8):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QColor("#fff3e0"))

        self.table.setSortingEnabled(True)

    def _format_date(self, date_str: str) -> str:
        """Форматирование даты"""
        if not date_str:
            return "Не указана"

        try:
            dt = QDateTime.fromString(date_str, "yyyy-MM-dd hh:mm:ss")
            if dt.isValid():
                return dt.toString("dd.MM.yyyy hh:mm")
            dt = QDateTime.fromString(date_str, "yyyy-MM-ddTHH:mm:ss")
            if dt.isValid():
                return dt.toString("dd.MM.yyyy hh:mm")
        except:
            pass

        return date_str

    def _on_selection_changed(self):
        """Обработчик выбора строки"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())

        self.toggle_ignore_btn.setEnabled(len(selected_rows) > 0)

    def _on_action_clicked(self):
        """Обработчик нажатия на кнопку действия"""
        button = self.sender()
        if not button:
            return

        result_id = button.property('result_id')
        is_ignored = button.property('is_ignored')

        new_status = not is_ignored
        if self.main_window.db_manager.set_ignored_status(result_id, new_status):
            self.ignore_toggled.emit(result_id, new_status)
            action = "установлено" if new_status else "снято"
            self.main_window.log_message(f"{action} игнорирование для результата ID:{result_id}")
            self.refresh_data()

    def _on_double_click(self, index):
        """Обработчик двойного клика"""
        row = index.row()
        id_item = self.table.item(row, 0)
        if id_item:
            result_id = id_item.data(Qt.UserRole)
            for result in self.all_results:
                if result.get('result_id') == result_id:
                    is_ignored = result.get('is_ignored', 0) == 1
                    new_status = not is_ignored
                    if self.main_window.db_manager.set_ignored_status(result_id, new_status):
                        self.ignore_toggled.emit(result_id, new_status)
                        self.refresh_data()
                    break

    def _toggle_selected_ignore(self):
        """Переключение статуса для выбранных строк"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            return

        for row in selected_rows:
            id_item = self.table.item(row, 0)
            if not id_item:
                continue

            result_id = id_item.data(Qt.UserRole)

            for result in self.all_results:
                if result.get('result_id') == result_id:
                    is_ignored = result.get('is_ignored', 0) == 1
                    new_status = not is_ignored

                    if self.main_window.db_manager.set_ignored_status(result_id, new_status):
                        self.ignore_toggled.emit(result_id, new_status)
                        action = "установлено" if new_status else "снято"
                        self.main_window.log_message(f"{action} игнорирование для результата ID:{result_id}")
                    break

        self.refresh_data()

    def _ignore_all_visible(self):
        """Игнорировать все видимые активные результаты"""
        active_ids = []
        for row in range(self.table.rowCount()):
            id_item = self.table.item(row, 0)
            status_item = self.table.item(row, 7)
            if id_item and status_item and "Активен" in status_item.text():
                active_ids.append(id_item.data(Qt.UserRole))

        if not active_ids:
            QMessageBox.information(self, "Информация", "Нет активных результатов для игнорирования")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы действительно хотите игнорировать все {len(active_ids)} активных результатов?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            updated = self.main_window.db_manager.set_ignored_status_batch(active_ids, True)

            for result_id in active_ids:
                self.main_window.excluded_ids.add(result_id)
                self.ignore_toggled.emit(result_id, True)

            self.main_window.log_message(f"Игнорировано {updated} результатов")
            self.refresh_data()

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

        toggle_action = menu.addAction("🔄 Сменить статус игнорирования")
        menu.addSeparator()
        refresh_action = menu.addAction("🔄 Обновить таблицу")

        action = menu.exec(self.table.mapToGlobal(position))

        if action == toggle_action:
            self._toggle_selected_ignore()
        elif action == refresh_action:
            self.refresh_data()

    def _set_quick_date_filter(self, period: str):
        """Установка быстрого фильтра дат"""
        from PySide6.QtCore import QDate

        today = QDate.currentDate()

        if period == 'today':
            self.search_widget.date_from_edit.setDate(today)
            self.search_widget.date_to_edit.setDate(today)
        elif period == 'week':
            self.search_widget.date_from_edit.setDate(today.addDays(-7))
            self.search_widget.date_to_edit.setDate(today)
        elif period == 'month':
            self.search_widget.date_from_edit.setDate(today.addMonths(-1))
            self.search_widget.date_to_edit.setDate(today)
        elif period == 'all':
            self.search_widget.date_from_edit.setDate(QDate(2000, 1, 1))
            self.search_widget.date_to_edit.setDate(today)

        # Применяем фильтр
        self.search_widget._apply_date_filter()