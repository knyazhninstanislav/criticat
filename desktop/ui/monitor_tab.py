from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QTextEdit, QPushButton, QLabel, QFrame)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont, QTextCursor, QColor
from criti_cat_logo import CritiCatLogo


class MonitorTab(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок с логотипом
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        # Логотип CritiCat
        logo_label = QLabel()
        logo_pixmap = CritiCatLogo.create_pixmap(80)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setFixedSize(80, 80)
        logo_label.setStyleSheet("background-color: transparent;")
        header_layout.addWidget(logo_label)

        # Заголовок
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(5)

        header = QLabel("🚨 CritiCat - система мониторинга критических значений")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2196F3;
            padding: 5px;
            background-color: transparent;
        """)
        header_text_layout.addWidget(header)

        # subtitle = QLabel("11111")
        # subtitle.setStyleSheet("""
        #     font-size: 11px;
        #     color: #7f8c8d;
        #     background-color: transparent;
        # """)
        # header_text_layout.addWidget(subtitle)

        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Остальной код без изменений...
        # Карточка с кнопками управления
        control_frame = QFrame()
        control_frame.setObjectName("controlFrame")
        control_frame.setStyleSheet("""
            QFrame#controlFrame {
                background-color: white;
                border: 1px solid #d5d8dc;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        control_layout = QHBoxLayout()

        self.manual_check_btn = QPushButton("🔍 ПРОВЕРИТЬ")
        self.manual_check_btn.clicked.connect(self.main_window.start_check)
        self.manual_check_btn.setMinimumHeight(40)
        self.manual_check_btn.setMinimumWidth(180)

        self.clear_log_btn = QPushButton("🗑️ Очистить")
        self.clear_log_btn.clicked.connect(self.clear_log)
        self.clear_log_btn.setMinimumHeight(40)
        self.clear_log_btn.setMinimumWidth(130)

        control_layout.addWidget(self.manual_check_btn)
        control_layout.addWidget(self.clear_log_btn)
        control_layout.addStretch()

        control_frame.setLayout(control_layout)
        layout.addWidget(control_frame)

        # Информационная панель
        info_frame = QFrame()
        info_frame.setObjectName("statsFrame")
        info_frame.setStyleSheet("""
            QFrame#statsFrame {
                background-color: #e8f5e9;
                border: 1px solid #a5d6a7;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        info_layout = QHBoxLayout()

        self.excluded_count_label = QLabel("Исключено результатов: 0")
        self.excluded_count_label.setStyleSheet("""
            color: #2e7d32;
            font-weight: bold;
            font-size: 12px;
            background-color: transparent;
        """)

        self.last_check_label = QLabel("Последняя проверка: -")
        self.last_check_label.setStyleSheet("""
            color: #558b2f;
            font-size: 11px;
            background-color: transparent;
        """)

        info_layout.addWidget(self.excluded_count_label)
        info_layout.addStretch()
        info_layout.addWidget(self.last_check_label)

        info_frame.setLayout(info_layout)
        layout.addWidget(info_frame)

        # Лог
        log_label = QLabel("📋 Лог выполнения:")
        log_label.setStyleSheet("""
            font-weight: bold;
            color: #5a6c7d;
            margin-top: 5px;
            font-size: 13px;
            background-color: transparent;
        """)
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)

        layout.addWidget(self.log_text)

        self.setLayout(layout)

    def add_log_message(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")

        if "Ошибка" in message:
            color = "#d32f2f"
        elif "Предупреждение" in message:
            color = "#f57c00"
        elif "Найдено" in message or "запущена" in message:
            color = "#1976d2"
        else:
            color = "#2e7d32"

        formatted_message = f'<span style="color: #666;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        self.log_text.append(formatted_message)

        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

        self.last_check_label.setText(f"Последняя активность: {timestamp}")

    def update_excluded_count(self, count: int):
        """Обновление счетчика исключенных результатов"""
        self.excluded_count_label.setText(f"Исключено результатов: {count}")

    def clear_log(self):
        """Очистка лога"""
        self.log_text.clear()
        self.add_log_message("Лог очищен")