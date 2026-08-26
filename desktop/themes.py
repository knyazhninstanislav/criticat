from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


class ThemeManager:
    """Менеджер тем оформления"""

    @staticmethod
    def get_light_palette() -> QPalette:
        """Светлая палитра"""
        palette = QPalette()

        # Основные цвета
        palette.setColor(QPalette.Window, QColor(245, 246, 250))
        palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(245, 246, 250))
        palette.setColor(QPalette.ToolTipBase, QColor(44, 62, 80))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(44, 62, 80))
        palette.setColor(QPalette.Button, QColor(236, 240, 241))
        palette.setColor(QPalette.ButtonText, QColor(44, 62, 80))
        palette.setColor(QPalette.BrightText, QColor(231, 76, 60))
        palette.setColor(QPalette.Link, QColor(33, 150, 243))
        palette.setColor(QPalette.Highlight, QColor(52, 152, 219))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

        # Дополнительные цвета
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 140, 141))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 140, 141))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 140, 141))

        return palette

    @staticmethod
    def get_dark_palette() -> QPalette:
        """Темная палитра"""
        palette = QPalette()

        # Основные цвета
        palette.setColor(QPalette.Window, QColor(30, 30, 35))
        palette.setColor(QPalette.WindowText, QColor(220, 220, 225))
        palette.setColor(QPalette.Base, QColor(45, 45, 50))
        palette.setColor(QPalette.AlternateBase, QColor(40, 40, 45))
        palette.setColor(QPalette.ToolTipBase, QColor(220, 220, 225))
        palette.setColor(QPalette.ToolTipText, QColor(30, 30, 35))
        palette.setColor(QPalette.Text, QColor(220, 220, 225))
        palette.setColor(QPalette.Button, QColor(55, 55, 60))
        palette.setColor(QPalette.ButtonText, QColor(220, 220, 225))
        palette.setColor(QPalette.BrightText, QColor(255, 82, 82))
        palette.setColor(QPalette.Link, QColor(66, 165, 245))
        palette.setColor(QPalette.Highlight, QColor(33, 150, 243))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

        # Дополнительные цвета
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 132))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 132))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 132))

        return palette

    @staticmethod
    def get_light_stylesheet() -> str:
        """Светлая тема оформления"""
        return """
            * {
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            QMainWindow {
                background-color: #f0f2f5;
            }

            QWidget {
                color: #2c3e50;
                font-size: 12px;
                background-color: transparent;
            }

            QWidget#centralWidget {
                background-color: #f0f2f5;
            }

            QTabWidget {
                background-color: #f0f2f5;
            }

            QTabWidget::pane {
                border: 1px solid #d5d8dc;
                background-color: #ffffff;
                border-radius: 5px;
                top: -1px;
            }

            QTabBar {
                background-color: transparent;
            }

            QTabBar::tab {
                background-color: #e8edf2;
                color: #5a6c7d;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: 600;
                font-size: 12px;
                border: 1px solid #d5d8dc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }

            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #2196F3;
                border-bottom: 2px solid #2196F3;
                font-weight: bold;
            }

            QTabBar::tab:hover:!selected {
                background-color: #d5dde5;
            }

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

            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 11px;
                min-height: 20px;
            }

            QPushButton:hover {
                background-color: #2980b9;
            }

            QPushButton:pressed {
                background-color: #1f6fa3;
            }

            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }

            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
                padding: 5px 8px;
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 12px;
                min-height: 20px;
                selection-background-color: #3498db;
                selection-color: white;
            }

            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, 
            QComboBox:focus, QDateEdit:focus {
                border-color: #3498db;
                background-color: #f7f9fc;
            }

            QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled,
            QComboBox:disabled, QDateEdit:disabled {
                background-color: #ecf0f1;
                color: #7f8c8d;
            }

            QListWidget, QTableWidget, QTextEdit {
                border: 1px solid #d5d8dc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #2c3e50;
                font-size: 11px;
                outline: none;
            }

            QListWidget::item {
                padding: 4px 8px;
                border-radius: 3px;
                margin: 1px 0px;
                color: #2c3e50;
            }

            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }

            QListWidget::item:hover:!selected {
                background-color: #edf2f7;
            }

            QTableWidget {
                gridline-color: #e0e0e0;
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

            QStatusBar {
                background-color: #ffffff;
                color: #2c3e50;
                border-top: 1px solid #d5d8dc;
                padding: 4px 8px;
            }

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

            QScrollBar:horizontal {
                background-color: #f0f2f5;
                height: 8px;
                border-radius: 4px;
            }

            QScrollBar::handle:horizontal {
                background-color: #bdc3c7;
                border-radius: 4px;
                min-width: 20px;
            }

            QToolTip {
                background-color: #34495e;
                color: white;
                border: 1px solid #2c3e50;
                padding: 5px 8px;
                border-radius: 3px;
                font-size: 11px;
            }

            QCheckBox {
                color: #2c3e50;
                font-size: 12px;
                spacing: 5px;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #d5d8dc;
                border-radius: 3px;
                background-color: #ffffff;
            }

            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }

            QLabel {
                color: #2c3e50;
                background-color: transparent;
            }

            QFrame {
                background-color: transparent;
            }

            QDialog {
                background-color: #ffffff;
            }
        """

    @staticmethod
    def get_dark_stylesheet() -> str:
        """Темная тема оформления"""
        return """
            * {
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            QMainWindow {
                background-color: #1e1e23;
            }

            QWidget {
                color: #dcdce1;
                font-size: 12px;
                background-color: transparent;
            }

            QWidget#centralWidget {
                background-color: #1e1e23;
            }

            QTabWidget {
                background-color: #1e1e23;
            }

            QTabWidget::pane {
                border: 1px solid #3a3a40;
                background-color: #2d2d32;
                border-radius: 5px;
                top: -1px;
            }

            QTabBar {
                background-color: transparent;
            }

            QTabBar::tab {
                background-color: #25252a;
                color: #a0a0a5;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: 600;
                font-size: 12px;
                border: 1px solid #3a3a40;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }

            QTabBar::tab:selected {
                background-color: #2d2d32;
                color: #42a5f5;
                border-bottom: 2px solid #42a5f5;
                font-weight: bold;
            }

            QTabBar::tab:hover:!selected {
                background-color: #35353a;
            }

            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #dcdce1;
                border: 1px solid #3a3a40;
                border-radius: 6px;
                margin-top: 8px;
                padding: 16px 10px 10px 10px;
                background-color: #2d2d32;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #42a5f5;
                background-color: #2d2d32;
            }

            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 11px;
                min-height: 20px;
            }

            QPushButton:hover {
                background-color: #1565c0;
            }

            QPushButton:pressed {
                background-color: #0d47a1;
            }

            QPushButton:disabled {
                background-color: #424242;
                color: #757575;
            }

            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
                padding: 5px 8px;
                border: 1px solid #3a3a40;
                border-radius: 4px;
                background-color: #1e1e23;
                color: #dcdce1;
                font-size: 12px;
                min-height: 20px;
                selection-background-color: #1976d2;
                selection-color: white;
            }

            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, 
            QComboBox:focus, QDateEdit:focus {
                border-color: #42a5f5;
                background-color: #25252a;
            }

            QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled,
            QComboBox:disabled, QDateEdit:disabled {
                background-color: #2a2a2f;
                color: #757575;
            }

            QListWidget, QTableWidget, QTextEdit {
                border: 1px solid #3a3a40;
                border-radius: 4px;
                background-color: #1e1e23;
                color: #dcdce1;
                font-size: 11px;
                outline: none;
            }

            QListWidget::item {
                padding: 4px 8px;
                border-radius: 3px;
                margin: 1px 0px;
                color: #dcdce1;
            }

            QListWidget::item:selected {
                background-color: #1976d2;
                color: white;
            }

            QListWidget::item:hover:!selected {
                background-color: #35353a;
            }

            QTableWidget {
                gridline-color: #3a3a40;
                alternate-background-color: #25252a;
            }

            QTableWidget::item {
                padding: 5px;
                color: #dcdce1;
                border-bottom: 1px solid #3a3a40;
            }

            QTableWidget::item:selected {
                background-color: #1e3a5f;
                color: #ffffff;
            }

            QHeaderView::section {
                background-color: #25252a;
                color: #dcdce1;
                font-weight: bold;
                font-size: 11px;
                padding: 8px;
                border: 1px solid #3a3a40;
                border-left: none;
                border-top: none;
            }

            QStatusBar {
                background-color: #2d2d32;
                color: #dcdce1;
                border-top: 1px solid #3a3a40;
                padding: 4px 8px;
            }

            QMenu {
                background-color: #2d2d32;
                color: #dcdce1;
                border: 1px solid #3a3a40;
                padding: 5px;
            }

            QMenu::item {
                padding: 8px 20px;
                border-radius: 3px;
            }

            QMenu::item:selected {
                background-color: #1976d2;
                color: white;
            }

            QScrollArea {
                border: none;
                background-color: transparent;
            }

            QScrollBar:vertical {
                background-color: #1e1e23;
                width: 8px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical {
                background-color: #55555a;
                border-radius: 4px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #6a6a6f;
            }

            QScrollBar:horizontal {
                background-color: #1e1e23;
                height: 8px;
                border-radius: 4px;
            }

            QScrollBar::handle:horizontal {
                background-color: #55555a;
                border-radius: 4px;
                min-width: 20px;
            }

            QToolTip {
                background-color: #dcdce1;
                color: #1e1e23;
                border: 1px solid #3a3a40;
                padding: 5px 8px;
                border-radius: 3px;
                font-size: 11px;
            }

            QCheckBox {
                color: #dcdce1;
                font-size: 12px;
                spacing: 5px;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #3a3a40;
                border-radius: 3px;
                background-color: #1e1e23;
            }

            QCheckBox::indicator:checked {
                background-color: #1976d2;
                border-color: #1565c0;
            }

            QLabel {
                color: #dcdce1;
                background-color: transparent;
            }

            QFrame {
                background-color: transparent;
            }

            QDialog {
                background-color: #2d2d32;
            }
        """


class ThemeController:
    """Контроллер переключения тем"""

    def __init__(self, app):
        self.app = app
        self.current_theme = 'light'

    def toggle_theme(self):
        """Переключение темы"""
        if self.current_theme == 'light':
            self.set_dark_theme()
        else:
            self.set_light_theme()

        return self.current_theme

    def set_light_theme(self):
        """Установка светлой темы"""
        self.current_theme = 'light'
        self.app.setPalette(ThemeManager.get_light_palette())
        self.app.setStyleSheet(ThemeManager.get_light_stylesheet())

    def set_dark_theme(self):
        """Установка темной темы"""
        self.current_theme = 'dark'
        self.app.setPalette(ThemeManager.get_dark_palette())
        self.app.setStyleSheet(ThemeManager.get_dark_stylesheet())

    def get_current_theme(self) -> str:
        """Получение текущей темы"""
        return self.current_theme

    def apply_theme(self, theme_name: str):
        """Применение указанной темы"""
        if theme_name == 'dark':
            self.set_dark_theme()
        else:
            self.set_light_theme()