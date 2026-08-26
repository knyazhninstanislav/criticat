def get_app_stylesheet() -> str:
    return """
    /* Полный сброс и установка светлой темы */
    * {
        background-color: transparent;
    }
    
    QMainWindow {
        background-color: #f5f6fa;
    }
    
    QWidget {
        color: #2c3e50;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 12px;
        background-color: transparent;
    }
    
    QWidget#centralWidget {
        background-color: #f5f6fa;
    }
    
    /* Стили вкладок */
    QTabWidget {
        background-color: #f5f6fa;
        border: none;
    }
    
    QTabWidget::pane {
        border: 1px solid #d5d8dc;
        background-color: #ffffff;
        border-radius: 6px;
        top: -1px;
    }
    
    QTabBar {
        background-color: transparent;
    }
    
    QTabBar::tab {
        background-color: #e8edf2;
        color: #5a6c7d;
        padding: 8px 20px;
        margin-right: 3px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
        font-weight: 600;
        font-size: 12px;
        border: 1px solid #d5d8dc;
        border-bottom: none;
    }
    
    QTabBar::tab:selected {
        background-color: #ffffff;
        color: #2196F3;
        border-bottom: 3px solid #2196F3;
        font-weight: bold;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #d5dde5;
        color: #2c3e50;
    }
    
    /* Группировка */
    QGroupBox {
        font-weight: bold;
        font-size: 12px;
        color: #2c3e50;
        border: 1px solid #d5d8dc;
        border-radius: 6px;
        margin-top: 8px;
        padding: 14px 8px 8px 8px;
        background-color: #ffffff;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
        color: #2196F3;
        background-color: #ffffff;
    }
    
    /* Кнопки */
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
    
    /* Поля ввода */
    QLineEdit {
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
    
    QLineEdit:focus {
        border-color: #3498db;
        background-color: #f7f9fc;
    }
    
    QLineEdit:disabled {
        background-color: #ecf0f1;
        color: #7f8c8d;
        border-color: #d5d8dc;
    }
    
    QSpinBox, QDoubleSpinBox {
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
    
    QSpinBox:focus, QDoubleSpinBox:focus {
        border-color: #3498db;
        background-color: #f7f9fc;
    }
    
    QSpinBox::up-button, QDoubleSpinBox::up-button {
        background-color: #ecf0f1;
        border-left: 1px solid #d5d8dc;
        border-bottom: 1px solid #d5d8dc;
        border-top-right-radius: 4px;
    }
    
    QSpinBox::down-button, QDoubleSpinBox::down-button {
        background-color: #ecf0f1;
        border-left: 1px solid #d5d8dc;
        border-bottom-right-radius: 4px;
    }
    
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 5px solid #2c3e50;
        width: 0;
        height: 0;
    }
    
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid #2c3e50;
        width: 0;
        height: 0;
    }
    
    /* Списки */
    QListWidget {
        border: 1px solid #d5d8dc;
        border-radius: 4px;
        background-color: #ffffff;
        padding: 4px;
        color: #2c3e50;
        font-size: 11px;
        outline: none;
    }
    
    QListWidget::item {
        padding: 4px 8px;
        border-radius: 3px;
        margin: 1px 0px;
        color: #2c3e50;
        background-color: transparent;
    }
    
    QListWidget::item:selected {
        background-color: #3498db;
        color: white;
    }
    
    QListWidget::item:hover:!selected {
        background-color: #edf2f7;
        color: #2c3e50;
    }
    
    /* Строка состояния */
    QStatusBar {
        background-color: #ffffff;
        color: #2c3e50;
        border-top: 1px solid #d5d8dc;
        padding: 4px 8px;
        font-size: 11px;
        min-height: 20px;
    }
    
    QStatusBar QLabel {
        color: #2c3e50;
    }
    
    /* Текстовый редактор для лога */
    QTextEdit {
        border: 1px solid #d5d8dc;
        border-radius: 5px;
        background-color: #fafbfc;
        color: #2c3e50;
        padding: 8px;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.4;
        selection-background-color: #3498db;
        selection-color: white;
    }
    
    /* Метки */
    QLabel {
        color: #2c3e50;
        background-color: transparent;
    }
    
    /* Рамки */
    QFrame {
        background-color: transparent;
    }
    
    /* Скроллбары */
    QScrollArea {
        border: none;
        background-color: transparent;
    }
    
    QScrollBar:vertical {
        background-color: #f0f2f5;
        width: 8px;
        border-radius: 4px;
        margin: 0;
    }
    
    QScrollBar::handle:vertical {
        background-color: #bdc3c7;
        border-radius: 4px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #95a5a6;
    }
    
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
        background: none;
    }
    
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {
        background: none;
    }
    
    QScrollBar:horizontal {
        background-color: #f0f2f5;
        height: 8px;
        border-radius: 4px;
        margin: 0;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #bdc3c7;
        border-radius: 4px;
        min-width: 20px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #95a5a6;
    }
    
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
        background: none;
    }
    
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {
        background: none;
    }
    
    /* Подсказки */
    QToolTip {
        background-color: #34495e;
        color: white;
        border: 1px solid #2c3e50;
        padding: 5px 8px;
        border-radius: 3px;
        font-size: 11px;
    }
    
    /* Диалоговые окна */
    QDialog {
        background-color: #ffffff;
    }
    
    /* Выпадающие списки */
    QComboBox {
        padding: 5px 8px;
        border: 1px solid #d5d8dc;
        border-radius: 4px;
        background-color: #ffffff;
        color: #2c3e50;
        font-size: 12px;
        min-height: 20px;
    }
    
    QComboBox:focus {
        border-color: #3498db;
    }
    
    QComboBox::drop-down {
        background-color: #ecf0f1;
        border-left: 1px solid #d5d8dc;
    }
    
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #2c3e50;
        selection-background-color: #3498db;
        selection-color: white;
    }
    
    /* Меню */
    QMenu {
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #d5d8dc;
    }
    
    QMenu::item {
        padding: 5px 20px;
    }
    
    QMenu::item:selected {
        background-color: #3498db;
        color: white;
    }
    """