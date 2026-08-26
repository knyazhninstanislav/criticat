from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QFrame, QScrollArea,
                               QWidget, QListWidget, QListWidgetItem,
                               QAbstractItemView, QStyledItemDelegate,
                               QStyle)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor, QPalette


class AlertDialog(QDialog):
    def __init__(self, results: list, parent=None):
        super().__init__(parent)
        self.results = results
        self.ignored_ids = set()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("⚠️ Критические значения!")

        # Устанавливаем размер окна
        if self.parent():
            parent_size = self.parent().size()
            self.resize(int(parent_size.width() * 0.7), int(parent_size.height() * 0.75))
        else:
            self.resize(650, 550)

        self.setModal(True)
        self.setStyleSheet("QDialog { background-color: #ffffff; }")

        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Компактный заголовок
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #fff3e0;
                border: 2px solid #ff9800;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        title = QLabel(f"⚠️ Обнаружены критические отклонения ({len(self.results)} тестов)")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #e65100;
            font-size: 14px;
            font-weight: bold;
            background-color: transparent;
        """)
        header_layout.addWidget(title)

        # Инструкция
        instruction = QLabel("Выберите результаты для игнорирования (Ctrl+Click для множественного выбора)")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setStyleSheet("""
            color: #bf360c;
            font-size: 11px;
            background-color: transparent;
        """)
        header_layout.addWidget(instruction)

        header.setLayout(header_layout)
        main_layout.addWidget(header)

        # Единый список всех результатов с группировкой по пациентам
        self.results_list = QListWidget()
        self.results_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.results_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.results_list.setUniformItemSizes(False)
        self.results_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                background-color: #fafbfc;
                padding: 5px;
                font-size: 11px;
            }
            QListWidget::item {
                border-bottom: 1px solid #e0e0e0;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #ffebee;
                border: 1px solid #ef5350;
                color: #2c3e50;
            }
        """)

        # Добавляем результаты, сгруппированные по пациентам
        self._populate_results()

        # Подключаем обработчик выбора
        self.results_list.itemSelectionChanged.connect(self._update_selection_info)

        main_layout.addWidget(self.results_list)

        # Панель с информацией и кнопками
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(5)

        # Информация о выборе
        info_layout = QHBoxLayout()
        self.selection_info = QLabel("Выбрано: 0 результатов у 0 пациентов")
        self.selection_info.setStyleSheet("""
            color: #5a6c7d;
            font-size: 11px;
            font-weight: bold;
            background-color: transparent;
        """)
        info_layout.addWidget(self.selection_info)
        info_layout.addStretch()
        bottom_layout.addLayout(info_layout)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        self.ignore_selected_btn = QPushButton("🚫 Игнорировать выбранные")
        self.ignore_selected_btn.setMinimumHeight(35)
        self.ignore_selected_btn.clicked.connect(self.ignore_selected)
        self.ignore_selected_btn.setEnabled(False)
        self.ignore_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 8px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)

        self.ignore_all_btn = QPushButton("✓ Игнорировать все")
        self.ignore_all_btn.setMinimumHeight(35)
        self.ignore_all_btn.clicked.connect(self.ignore_all)
        self.ignore_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 8px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)

        self.cancel_btn = QPushButton("✗ Закрыть")
        self.cancel_btn.setMinimumHeight(35)
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border-radius: 4px;
                padding: 8px 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)

        buttons_layout.addWidget(self.ignore_selected_btn)
        buttons_layout.addWidget(self.ignore_all_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)

        bottom_layout.addLayout(buttons_layout)
        bottom_frame.setLayout(bottom_layout)
        main_layout.addWidget(bottom_frame)

        self.setLayout(main_layout)

    def _populate_results(self):
        """Заполнение списка результатов с группировкой по пациентам"""
        # Группируем по пациентам
        grouped = {}
        for result in self.results:
            patient_key = f"{result.get('full_name', 'Неизвестно')}|{result.get('ids', 'Н/Д')}"
            if patient_key not in grouped:
                grouped[patient_key] = {
                    'department': result.get('department', 'Не указано'),
                    'results': []
                }
            grouped[patient_key]['results'].append(result)

        # Добавляем в список
        for patient_key, patient_data in grouped.items():
            full_name, ids = patient_key.split('|')
            department = patient_data['department']
            patient_results = patient_data['results']

            # Добавляем заголовок пациента с отделением
            header_item = QListWidgetItem()
            header_item.setFlags(Qt.NoItemFlags)  # Нельзя выбрать
            header_item.setData(Qt.UserRole, None)  # Нет ID результата
            header_widget = PatientHeaderWidget(full_name, ids, department, len(patient_results))
            header_item.setSizeHint(QSize(0, 45))  # Уменьшаем высоту до 45px
            self.results_list.addItem(header_item)
            self.results_list.setItemWidget(header_item, header_widget)

            # Добавляем результаты пациента
            for result in patient_results:
                result_item = QListWidgetItem()
                result_item.setData(Qt.UserRole, result.get('id'))
                result_widget = ResultItemWidget(result)
                result_item.setSizeHint(QSize(0, 50))
                self.results_list.addItem(result_item)
                self.results_list.setItemWidget(result_item, result_widget)

    def _update_selection_info(self):
        """Обновление информации о выбранных элементах"""
        selected_items = self.results_list.selectedItems()
        selected_count = len([item for item in selected_items if item.data(Qt.UserRole) is not None])

        # Считаем уникальных пациентов
        selected_patients = set()
        current_patient = None
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            if item.data(Qt.UserRole) is None:  # Это заголовок пациента
                header_widget = self.results_list.itemWidget(item)
                if header_widget:
                    current_patient = header_widget.patient_name
            elif item.isSelected() and current_patient:
                selected_patients.add(current_patient)

        self.selection_info.setText(f"Выбрано: {selected_count} результатов у {len(selected_patients)} пациентов")
        self.ignore_selected_btn.setEnabled(selected_count > 0)

    def ignore_selected(self):
        """Игнорировать выбранные результаты"""
        for item in self.results_list.selectedItems():
            result_id = item.data(Qt.UserRole)
            if result_id is not None:
                self.ignored_ids.add(result_id)
        self.accept()

    def ignore_all(self):
        """Игнорировать все результаты"""
        for result in self.results:
            self.ignored_ids.add(result.get('id'))
        self.accept()

    def get_ignored_ids(self):
        """Получить список ID для игнорирования"""
        return list(self.ignored_ids)


class PatientHeaderWidget(QWidget):
    """Виджет заголовка пациента с отображением отделения"""

    def __init__(self, full_name: str, ids: str, department: str, test_count: int):
        super().__init__()
        self.patient_name = full_name

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)

        # Верхняя строка - ФИО и ID
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        patient_label = QLabel(f"👤 {full_name}")
        patient_label.setStyleSheet("""
            color: #1565c0;
            font-size: 13px;
            font-weight: bold;
            background-color: transparent;
            padding: 2px 0px;
        """)
        top_layout.addWidget(patient_label)

        ids_label = QLabel(f"ID: {ids}")
        ids_label.setStyleSheet("""
            color: #1976d2;
            font-size: 12px;
            background-color: transparent;
            padding: 2px 0px;
        """)
        top_layout.addWidget(ids_label)

        top_layout.addStretch()

        count_label = QLabel(f"Тестов: {test_count}")
        count_label.setStyleSheet("""
            color: #1976d2;
            font-size: 11px;
            background-color: transparent;
            padding: 2px 0px;
        """)
        top_layout.addWidget(count_label)

        layout.addLayout(top_layout)

        # Нижняя строка - отделение
        bottom_layout = QHBoxLayout()

        dept_label = QLabel(f"🏥 {department}")
        dept_label.setStyleSheet("""
            color: #1565c0;
            font-size: 8px;  /* Уменьшенный шрифт */
            font-weight: bold;
            background-color: #bbdefb;
            border: 1px solid #64b5f6;
            border-radius: 4px;
            padding: 3px 8px;
            margin-top: 2px;
        """)
        bottom_layout.addWidget(dept_label)
        bottom_layout.addStretch()

        layout.addLayout(bottom_layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 5px;
            }
        """)

        # Устанавливаем минимальную высоту виджета
        self.setMinimumHeight(50)

        self.setLayout(layout)


class ResultItemWidget(QWidget):
    """Компактный виджет одного результата без отображения отделения"""

    def __init__(self, result: dict):
        super().__init__()
        self.result = result

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(3)

        # Верхняя строка - название теста
        test_name = QLabel(f"🧪 {result.get('test_name', 'Тест')}")
        test_name.setStyleSheet("""
            color: #2c3e50;
            font-size: 11px;
            font-weight: bold;
            background-color: transparent;
        """)
        layout.addWidget(test_name)

        # Нижняя строка - значение, норма и отклонение
        value_layout = QHBoxLayout()
        value_layout.setSpacing(8)

        value = result.get('result_value', 0)
        ref_lower = result.get('ref_lower', 0)
        ref_upper = result.get('ref_upper', 0)

        # Определяем тип отклонения
        if value > ref_upper:
            deviation = ((value - ref_upper) / ref_upper) * 100
            value_text = f"⬆️ {value:.2f}"
            deviation_text = f"+{deviation:.1f}%"
        else:
            deviation = ((ref_lower - value) / ref_lower) * 100
            value_text = f"⬇️ {value:.2f}"
            deviation_text = f"-{deviation:.1f}%"

        value_label = QLabel(value_text)
        value_label.setStyleSheet("""
            color: #d32f2f;
            font-size: 13px;
            font-weight: bold;
            background-color: transparent;
        """)
        value_layout.addWidget(value_label)

        ref_label = QLabel(f"(норма: {ref_lower:.2f}-{ref_upper:.2f})")
        ref_label.setStyleSheet("""
            color: #666;
            font-size: 10px;
            background-color: transparent;
        """)
        value_layout.addWidget(ref_label)
        value_layout.addStretch()

        # Отклонение
        deviation_label = QLabel(deviation_text)
        deviation_label.setStyleSheet("""
            color: #c62828;
            font-size: 11px;
            font-weight: bold;
            background-color: transparent;
        """)
        deviation_label.setAlignment(Qt.AlignRight)
        value_layout.addWidget(deviation_label)

        layout.addLayout(value_layout)

        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)

        self.setLayout(layout)