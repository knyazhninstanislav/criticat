from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import (QPixmap, QPainter, QColor, QBrush, QPen,
                           QLinearGradient, QRadialGradient, QIcon)
import math


class CritiCatLogo:
    """Класс для отрисовки логотипа CritiCat"""

    @staticmethod
    def create_pixmap(size: int = 200) -> QPixmap:
        """Создание pixmap с логотипом CritiCat"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        CritiCatLogo.draw_logo(painter, size / 2, size / 2, size * 0.9)

        painter.end()
        return pixmap

    @staticmethod
    def create_icon(size: int = 64) -> QIcon:
        """Создание иконки с логотипом"""
        return QIcon(CritiCatLogo.create_pixmap(size))

    @staticmethod
    def draw_logo(painter: QPainter, center_x: float, center_y: float, size: float):
        """Рисование логотипа CritiCat в указанном месте"""

        # Масштабируем координаты из SVG (0-200) в наш размер
        scale = size / 200.0
        offset_x = center_x - 100 * scale
        offset_y = center_y - 100 * scale

        def svg_x(x):
            return offset_x + x * scale

        def svg_y(y):
            return offset_y + y * scale

        def svg_point(x, y):
            return QPoint(int(svg_x(x)), int(svg_y(y)))

        # Цвета
        red_color = QColor("#ff2d55")
        light_red = QColor("#ff6b8a")
        green_color = QColor("#00ff94")

        # Уши
        ear_pen = QPen(red_color, max(1, 4 * scale))
        painter.setPen(ear_pen)
        painter.setBrush(Qt.NoBrush)

        # Левое ухо
        left_ear_points = [
            svg_point(30, 40),
            svg_point(70, 10),
            svg_point(90, 55)
        ]
        painter.drawPolygon(left_ear_points)

        # Правое ухо
        right_ear_points = [
            svg_point(170, 40),
            svg_point(130, 10),
            svg_point(110, 55)
        ]
        painter.drawPolygon(right_ear_points)

        # Голова
        painter.drawRoundedRect(
            int(svg_x(25)), int(svg_y(25)),
            int(150 * scale), int(140 * scale),
            int(30 * scale), int(30 * scale)
        )

        # Глаза
        eye_pen = QPen(red_color, max(1, 3 * scale))
        painter.setPen(eye_pen)

        # Левый глаз
        painter.drawEllipse(
            svg_point(65, 80),
            int(14 * scale), int(14 * scale)
        )

        # Зрачок левого глаза
        painter.setBrush(QBrush(red_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            svg_point(68, 77),
            int(4 * scale), int(4 * scale)
        )

        # Правый глаз
        painter.setBrush(Qt.NoBrush)
        painter.setPen(eye_pen)
        painter.drawEllipse(
            svg_point(135, 80),
            int(14 * scale), int(14 * scale)
        )

        # Зрачок правого глаза
        painter.setBrush(QBrush(red_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            svg_point(138, 77),
            int(4 * scale), int(4 * scale)
        )

        # Нос
        painter.setBrush(QBrush(red_color))
        painter.setPen(Qt.NoPen)
        nose_points = [
            svg_point(100, 95),
            svg_point(94, 108),
            svg_point(106, 108)
        ]
        painter.drawPolygon(nose_points)

        # Усы
        whisker_color = QColor(255, 255, 255, 64)
        whisker_pen = QPen(whisker_color, max(1, 2 * scale))
        painter.setPen(whisker_pen)
        painter.setBrush(Qt.NoBrush)

        # Левые усы
        painter.drawLine(svg_point(30, 105), svg_point(75, 110))
        painter.drawLine(svg_point(30, 120), svg_point(78, 118))

        # Правые усы
        painter.drawLine(svg_point(170, 105), svg_point(125, 110))
        painter.drawLine(svg_point(170, 120), svg_point(122, 118))

        # ECG линия (зеленая)
        ecg_pen = QPen(green_color, max(1, 3 * scale))
        ecg_pen.setCapStyle(Qt.RoundCap)
        ecg_pen.setJoinStyle(Qt.RoundJoin)

        # Точки ECG
        ecg_points = [
            (25, 60), (50, 60), (58, 40), (66, 80), (74, 30),
            (82, 70), (90, 55), (98, 90), (106, 45), (114, 85),
            (122, 50), (130, 70), (138, 45), (146, 75), (154, 55), (175, 60)
        ]

        # Свечение
        glow_color = QColor(0, 255, 148, 80)
        glow_pen = QPen(glow_color, max(1, 5 * scale))
        glow_pen.setCapStyle(Qt.RoundCap)
        glow_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.NoBrush)

        points = []
        for x, y in ecg_points:
            points.append(svg_point(x, y))

        painter.drawPolyline(points)

        # Основная линия
        painter.setPen(ecg_pen)
        painter.drawPolyline(points)

        # Уголки сканирования
        corner_color = QColor(255, 107, 138, 128)
        corner_pen = QPen(corner_color, max(1, 2 * scale))
        painter.setPen(corner_pen)
        painter.setBrush(Qt.NoBrush)

        # Верхний левый
        painter.drawRect(int(svg_x(10)), int(svg_y(10)), int(12 * scale), int(12 * scale))
        # Верхний правый
        painter.drawRect(int(svg_x(178)), int(svg_y(10)), int(12 * scale), int(12 * scale))
        # Нижний левый
        painter.drawRect(int(svg_x(10)), int(svg_y(178)), int(12 * scale), int(12 * scale))
        # Нижний правый
        painter.drawRect(int(svg_x(178)), int(svg_y(178)), int(12 * scale), int(12 * scale))

    @staticmethod
    def draw_splash_background(painter: QPainter, width: int, height: int):
        """Рисование фона для сплэш-скрина"""
        bg_gradient = QRadialGradient(width / 2, height / 2, max(width, height) / 2)
        bg_gradient.setColorAt(0, QColor("#1a1e2e"))
        bg_gradient.setColorAt(1, QColor("#0b0e14"))
        painter.setBrush(QBrush(bg_gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, width, height, 20, 20)

    # В конец файла добавляем метод для создания ICO

    @staticmethod
    def create_ico_file(filename: str = "criticat.ico"):
        """Создание ICO файла с логотипом"""
        try:
            from PIL import Image, ImageDraw
            import math

            # Создаем изображения разных размеров
            sizes = [16, 32, 48, 64, 128, 256]
            images = []

            for size in sizes:
                # Создаем pixmap
                pixmap = CritiCatLogo.create_pixmap(size)

                # Конвертируем в PIL Image
                pixmap.save(f"temp_icon_{size}.png")
                img = Image.open(f"temp_icon_{size}.png")
                images.append(img)

                # Удаляем временный файл
                import os
                os.remove(f"temp_icon_{size}.png")

            # Сохраняем как ICO
            images[0].save(filename, format='ICO', sizes=[(s, s) for s in sizes], append_images=images[1:])
            print(f"ICO файл создан: {filename}")
            return True

        except ImportError:
            print("Pillow не установлен. Установите: pip install Pillow")
            return False
        except Exception as e:
            print(f"Ошибка создания ICO: {e}")
            return False


# Для обратной совместимости
def create_logo_pixmap(size: int = 200) -> QPixmap:
    """Функция для создания pixmap с логотипом"""
    return CritiCatLogo.create_pixmap(size)


def create_logo_icon(size: int = 64) -> QIcon:
    """Функция для создания иконки с логотипом"""
    return CritiCatLogo.create_icon(size)