from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLineEdit, QPushButton, QLabel, QFrame,
                               QComboBox, QListWidget, QListWidgetItem,
                               QDateEdit, QCheckBox)
from PySide6.QtCore import Qt, Signal, QTimer, QDate
from PySide6.QtGui import QFont, QColor


class SearchWidget(QWidget):
    """Виджет полнотекстового поиска с фильтром по датам"""
    search_requested = Signal(dict)  # Сигнал с параметрами поиска
    search_cleared = Signal()
    date_filter_changed = Signal(dict)  # Сигнал изменения фильтра дат

    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)

        # Основная строка поиска
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                padding: 3px;
            }
            QFrame:focus-within {
                border-color: #3498db;
            }
        """)
        search_layout = QHBoxLayout()
        search_layout.setSpacing(3)
        search_layout.setContentsMargins(3, 3, 3, 3)

        # Иконка поиска
        search_icon = QLabel("🔍")
        search_icon.setFixedSize(16, 16)
        search_icon.setStyleSheet("""
            font-size: 10px;
            background-color: transparent;
            padding: 0px;
        """)
        search_layout.addWidget(search_icon)

        # Поле ввода
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по ФИО, IDS, отделению, тесту...")
        self.search_input.setMinimumHeight(22)
        self.search_input.setMaximumHeight(24)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background-color: transparent;
                color: #2c3e50;
                font-size: 11px;
                padding: 2px;
            }
            QLineEdit:focus {
                border: none;
                background-color: transparent;
            }
        """)
        self.search_input.textChanged.connect(self._on_text_changed)
        search_layout.addWidget(self.search_input)

        # Кнопка очистки
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(15, 15)
        self.clear_btn.setVisible(False)
        self.clear_btn.clicked.connect(self.clear_search)
        self.clear_btn.setToolTip("Очистить поиск")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: #666;
                border: none;
                border-radius: 7px;
                font-weight: bold;
                font-size: 8px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        search_layout.addWidget(self.clear_btn)

        search_frame.setLayout(search_layout)
        layout.addWidget(search_frame)

        # Фильтры поиска и дат
        filters_frame = QFrame()
        filters_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(5)
        filters_layout.setContentsMargins(0, 2, 0, 0)

        # Выбор типа поиска
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItem("Все поля", "all")
        self.search_type_combo.addItem("ФИО", "full_name")
        self.search_type_combo.addItem("IDS", "ids")
        self.search_type_combo.addItem("Отделение", "department")
        self.search_type_combo.addItem("Тест", "test_name")
        self.search_type_combo.setMaximumHeight(22)
        self.search_type_combo.setStyleSheet("""
            QComboBox {
                padding: 2px 5px;
                border: 1px solid #d5d8dc;
                border-radius: 3px;
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 10px;
                min-height: 18px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                background-color: #ecf0f1;
                border-left: 1px solid #d5d8dc;
                width: 15px;
            }
        """)
        filters_layout.addWidget(self.search_type_combo)

        # Чувствительность к регистру
        self.case_sensitive_cb = QPushButton("Aa")
        self.case_sensitive_cb.setCheckable(True)
        self.case_sensitive_cb.setFixedSize(20, 20)
        self.case_sensitive_cb.setToolTip("Учитывать регистр")
        self.case_sensitive_cb.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #666;
                border: 1px solid #d5d8dc;
                border-radius: 3px;
                font-weight: bold;
                font-size: 8px;
                padding: 0px;
            }
            QPushButton:checked {
                background-color: #3498db;
                color: white;
                border-color: #2980b9;
            }
        """)
        filters_layout.addWidget(self.case_sensitive_cb)

        # Точное совпадение
        self.exact_match_cb = QPushButton("=")
        self.exact_match_cb.setCheckable(True)
        self.exact_match_cb.setFixedSize(20, 20)
        self.exact_match_cb.setToolTip("Точное совпадение")
        self.exact_match_cb.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #666;
                border: 1px solid #d5d8dc;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
                padding: 0px;
            }
            QPushButton:checked {
                background-color: #e67e22;
                color: white;
                border-color: #d35400;
            }
        """)
        filters_layout.addWidget(self.exact_match_cb)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("""
            QFrame {
                color: #d5d8dc;
                background-color: #d5d8dc;
                max-width: 1px;
                max-height: 20px;
                margin: 0px 5px;
            }
        """)
        filters_layout.addWidget(separator)

        # Фильтр по датам
        date_label = QLabel("📅")
        date_label.setFixedSize(16, 16)
        date_label.setStyleSheet("""
            font-size: 10px;
            background-color: transparent;
        """)
        filters_layout.addWidget(date_label)

        # Дата от
        self.date_from_edit = QDateEdit()
        self.date_from_edit.setCalendarPopup(True)
        self.date_from_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_from_edit.setDate(QDate.currentDate().addMonths(-1))
        self.date_from_edit.setMaximumHeight(22)
        self.date_from_edit.setMaximumWidth(90)
        self.date_from_edit.setStyleSheet("""
            QDateEdit {
                padding: 2px 5px;
                border: 1px solid #d5d8dc;
                border-radius: 3px;
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 10px;
                min-height: 18px;
            }
            QDateEdit:focus {
                border-color: #3498db;
            }
            QDateEdit::drop-down {
                background-color: #ecf0f1;
                border-left: 1px solid #d5d8dc;
                width: 15px;
            }
        """)
        filters_layout.addWidget(self.date_from_edit)

        # Разделитель "до"
        to_label = QLabel("-")
        to_label.setStyleSheet("""
            color: #666;
            font-size: 10px;
            background-color: transparent;
            padding: 0px 2px;
        """)
        filters_layout.addWidget(to_label)

        # Дата до
        self.date_to_edit = QDateEdit()
        self.date_to_edit.setCalendarPopup(True)
        self.date_to_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_to_edit.setDate(QDate.currentDate())
        self.date_to_edit.setMaximumHeight(22)
        self.date_to_edit.setMaximumWidth(90)
        self.date_to_edit.setStyleSheet("""
            QDateEdit {
                padding: 2px 5px;
                border: 1px solid #d5d8dc;
                border-radius: 3px;
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 10px;
                min-height: 18px;
            }
            QDateEdit:focus {
                border-color: #3498db;
            }
            QDateEdit::drop-down {
                background-color: #ecf0f1;
                border-left: 1px solid #d5d8dc;
                width: 15px;
            }
        """)
        filters_layout.addWidget(self.date_to_edit)

        # Кнопка применения фильтра дат
        self.apply_date_btn = QPushButton("Применить")
        self.apply_date_btn.setFixedHeight(22)
        self.apply_date_btn.setMaximumWidth(70)
        self.apply_date_btn.clicked.connect(self._apply_date_filter)
        self.apply_date_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                font-size: 9px;
                border-radius: 3px;
                padding: 2px 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        filters_layout.addWidget(self.apply_date_btn)

        # Кнопка сброса дат
        self.reset_date_btn = QPushButton("Сброс")
        self.reset_date_btn.setFixedHeight(22)
        self.reset_date_btn.setMaximumWidth(50)
        self.reset_date_btn.clicked.connect(self._reset_date_filter)
        self.reset_date_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                font-size: 9px;
                border-radius: 3px;
                padding: 2px 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        filters_layout.addWidget(self.reset_date_btn)

        filters_layout.addStretch()

        # Счетчик результатов
        self.results_count_label = QLabel("")
        self.results_count_label.setStyleSheet("""
            color: #7f8c8d;
            font-size: 9px;
            background-color: transparent;
            padding: 0px 3px;
        """)
        filters_layout.addWidget(self.results_count_label)

        filters_frame.setLayout(filters_layout)
        layout.addWidget(filters_frame)

        self.setLayout(layout)

        # Подключаем сигналы изменения дат
        self.date_from_edit.dateChanged.connect(self._on_date_changed)
        self.date_to_edit.dateChanged.connect(self._on_date_changed)

    def _on_date_changed(self, date):
        """Обработчик изменения даты"""
        # Проверяем, что дата "от" не больше даты "до"
        if self.date_from_edit.date() > self.date_to_edit.date():
            if self.sender() == self.date_from_edit:
                self.date_to_edit.setDate(self.date_from_edit.date())
            else:
                self.date_from_edit.setDate(self.date_to_edit.date())

    def _apply_date_filter(self):
        """Применение фильтра по датам"""
        date_filter = {
            'date_from': self.date_from_edit.date().toPython(),
            'date_to': self.date_to_edit.date().toPython()
        }
        self.date_filter_changed.emit(date_filter)

    def _reset_date_filter(self):
        """Сброс фильтра по датам"""
        self.date_from_edit.setDate(QDate.currentDate().addMonths(-1))
        self.date_to_edit.setDate(QDate.currentDate())
        self.date_filter_changed.emit(None)

    def get_date_filter(self) -> dict:
        """Получение текущего фильтра дат"""
        return {
            'date_from': self.date_from_edit.date().toPython(),
            'date_to': self.date_to_edit.date().toPython()
        }

    def _on_text_changed(self, text):
        """Обработчик изменения текста"""
        self.clear_btn.setVisible(bool(text))
        self.search_timer.stop()
        self.search_timer.start(300)

    def _perform_search(self):
        """Выполнение поиска"""
        search_text = self.search_input.text().strip()

        if not search_text:
            self.clear_search()
            return

        search_params = {
            'text': search_text,
            'type': self.search_type_combo.currentData(),
            'case_sensitive': self.case_sensitive_cb.isChecked(),
            'exact_match': self.exact_match_cb.isChecked()
        }

        self.search_requested.emit(search_params)

    def clear_search(self):
        """Очистка поиска"""
        self.search_input.clear()
        self.clear_btn.setVisible(False)
        self.results_count_label.setText("")
        self.search_cleared.emit()

    def set_results_count(self, count: int):
        """Установка количества найденных результатов"""
        if count >= 0:
            self.results_count_label.setText(f"Найдено: {count}")
        else:
            self.results_count_label.setText("")

    def get_search_params(self) -> dict:
        """Получение текущих параметров поиска"""
        text = self.search_input.text().strip()
        if not text:
            return None

        return {
            'text': text,
            'type': self.search_type_combo.currentData(),
            'case_sensitive': self.case_sensitive_cb.isChecked(),
            'exact_match': self.exact_match_cb.isChecked()
        }