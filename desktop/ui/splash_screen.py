from PySide6.QtWidgets import QSplashScreen
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import (QPixmap, QPainter, QColor, QBrush, QPen, QFont,
                           QLinearGradient, QRadialGradient)
from ui.criti_cat_logo import CritiCatLogo


class CritiCatSplashScreen(QSplashScreen):
    """Сплэш-скрин с логотипом CritiCat"""

    def __init__(self):
        pixmap = self._create_splash_pixmap()
        super().__init__(pixmap)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.close_timer = QTimer()
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self._start_fade_out)

        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._update_pulse)
        self.pulse_phase = 0

        self.progress = 0
        self.loading_steps = [
            "Подключение к базе данных...",
            "Загрузка настроек...",
            "Инициализация Telegram...",
            "Проверка обновлений...",
            "Запуск системы..."
        ]
        self.current_step = 0

        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self._update_loading)

        self.animation = None

    def _create_splash_pixmap(self) -> QPixmap:
        """Создание pixmap для сплэш-скрина"""
        size = 500
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Фон
        CritiCatLogo.draw_splash_background(painter, size, size)

        # Логотип (смещен вверх)
        CritiCatLogo.draw_logo(painter, size / 2, size / 2 - 60, 160)

        # Текст CRITICAT
        text_font = QFont("Segoe UI", 32, QFont.Bold)
        text_font.setLetterSpacing(QFont.AbsoluteSpacing, 5)
        painter.setFont(text_font)

        text_gradient = QLinearGradient(size / 2 - 100, 0, size / 2 + 100, 0)
        text_gradient.setColorAt(0, QColor("#ff2d55"))
        text_gradient.setColorAt(1, QColor("#ff6b8a"))
        painter.setPen(QPen(QBrush(text_gradient), 1))

        criticat_y = int(size / 2 + 50)
        painter.drawText(0, criticat_y, size, 50, Qt.AlignCenter, "CRITICAT")

        # Подзаголовок
        sub_font = QFont("Segoe UI", 11, QFont.Normal)
        sub_font.setLetterSpacing(QFont.AbsoluteSpacing, 6)
        painter.setFont(sub_font)
        painter.setPen(QColor(255, 255, 255, 80))

        sub_y = criticat_y + 40
        painter.drawText(0, sub_y, size, 20, Qt.AlignCenter, "CRITICAL ALERT SYSTEM")

        # Версия
        version_font = QFont("Segoe UI", 9, QFont.Normal)
        painter.setFont(version_font)
        painter.setPen(QColor(255, 255, 255, 50))
        painter.drawText(size - 80, size - 25, 60, 20, Qt.AlignRight, "v1.0.0")

        painter.end()
        return pixmap

    def show_splash(self, duration_ms: int = 5000):
        """Показ сплэш-скрина"""
        self.show()
        self.pulse_timer.start(50)
        self.loading_timer.start(500)
        self.close_timer.start(duration_ms)

    def _update_pulse(self):
        """Обновление пульсации"""
        self.pulse_phase += 0.1
        self.repaint()

    def _update_loading(self):
        """Обновление прогресса загрузки"""
        if self.current_step < len(self.loading_steps):
            self.progress = (self.current_step + 1) / len(self.loading_steps) * 100
            self.current_step += 1
            self.repaint()

    def _start_fade_out(self):
        """Начало анимации исчезновения"""
        self.pulse_timer.stop()
        self.loading_timer.stop()

        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.finished.connect(self.close)
        self.animation.start()

    def paintEvent(self, event):
        """Переопределяем для отображения прогресса"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Прогресс-бар
        bar_width = 300
        bar_height = 4
        bar_x = (self.width() - bar_width) // 2
        bar_y = self.height() - 70

        # Статус
        if self.current_step < len(self.loading_steps):
            status_text = self.loading_steps[self.current_step]
            painter.setPen(QColor(255, 255, 255, 180))
            font = QFont("Segoe UI", 10)
            painter.setFont(font)
            painter.drawText(0, bar_y - 25, self.width(), 20, Qt.AlignCenter, status_text)

        # Фон прогресс-бара
        painter.setBrush(QColor(255, 255, 255, 30))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 2, 2)

        # Заполнение
        fill_width = int(bar_width * (self.progress / 100))
        if fill_width > 0:
            gradient = QLinearGradient(bar_x, 0, bar_x + bar_width, 0)
            gradient.setColorAt(0, QColor("#ff2d55"))
            gradient.setColorAt(1, QColor("#00ff94"))
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(bar_x, bar_y, fill_width, bar_height, 2, 2)

        # Процент
        percent_text = f"{int(self.progress)}%"
        painter.setPen(QColor(255, 255, 255, 100))
        percent_font = QFont("Segoe UI", 9)
        painter.setFont(percent_font)
        painter.drawText(bar_x + bar_width + 10, bar_y - 5, 50, 15, Qt.AlignLeft, percent_text)


class SplashController:
    """Контроллер сплэш-скрина"""

    def __init__(self):
        self.splash = None

    def show(self, duration_ms: int = 5000):
        """Показать сплэш-скрин"""
        self.splash = CritiCatSplashScreen()
        self.splash.show_splash(duration_ms)
        return self.splash

    def close(self):
        """Закрыть сплэш-скрин"""
        if self.splash:
            self.splash.close()
            self.splash = None