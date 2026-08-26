from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QTableWidget, QTableWidgetItem, QPushButton,
                               QLabel, QHeaderView, QFrame, QAbstractItemView,
                               QCheckBox, QDoubleSpinBox, QMessageBox,
                               QWidget, QComboBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont


class TestSettingsDialog(QDialog):
    """Диалог настройки проверяемых тестов"""
    settings_saved = Signal(dict)

    def __init__(self, db_manager, current_settings: dict, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_settings = current_settings or {}
        self.test_settings = {}
        self.init_ui()
        self.load_tests()

    def init_ui(self):
        self.setWindowTitle("Настройка проверяемых тестов")
        self.setMinimumSize(900, 600)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок
        header = QLabel("🧪 Настройка проверяемых тестов")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2196F3;
            padding: 5px;
            background-color: transparent;
        """)
        layout.addWidget(header)

        # Информация
        info = QLabel("Отметьте тесты для мониторинга, выберите тип отслеживания и укажите пороги")
        info.setStyleSheet("""
            color: #7f8c8d;
            font-size: 12px;
            background-color: transparent;
        """)
        layout.addWidget(info)

        # Таблица тестов
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Мониторинг", "Тест", "Тип отслеживания",
            "Нижний порог", "Верхний порог", "Статус", "Описание"
        ])

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        header_view = self.table.horizontalHeader()
        header_view.setStretchLastSection(True)
        header_view.setSectionResizeMode(QHeaderView.Interactive)
        header_view.setDefaultAlignment(Qt.AlignCenter)

        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 200)

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
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-weight: bold;
                font-size: 11px;
                padding: 8px;
                border: 1px solid #d5d8dc;
            }
        """)

        layout.addWidget(self.table)

        # Кнопки управления
        control_frame = QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        self.select_all_btn = QPushButton("✓ Выбрать все")
        self.select_all_btn.clicked.connect(self.select_all_tests)
        self.select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        self.deselect_all_btn = QPushButton("✗ Снять все")
        self.deselect_all_btn.clicked.connect(self.deselect_all_tests)
        self.deselect_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)

        self.reset_defaults_btn = QPushButton("🔄 Сбросить пороги")
        self.reset_defaults_btn.clicked.connect(self.reset_thresholds)
        self.reset_defaults_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)

        control_layout.addWidget(self.select_all_btn)
        control_layout.addWidget(self.deselect_all_btn)
        control_layout.addWidget(self.reset_defaults_btn)
        control_layout.addStretch()

        control_frame.setLayout(control_layout)
        layout.addWidget(control_frame)

        # Кнопки сохранения
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.save_btn = QPushButton("💾 Сохранить настройки")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)

        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_tests(self):
        """Загрузка списка тестов из БД с сохраненными настройками"""
        if not self.db_manager.is_connected():
            QMessageBox.warning(self, "Предупреждение", "Нет подключения к БД")
            return

        test_names = self.db_manager.get_all_test_names()
        ref_values = self.db_manager.get_test_reference_values()

        print(f"Загружено тестов: {len(test_names)}")
        print(f"Сохраненные настройки: {self.current_settings}")

        self.table.setRowCount(len(test_names))
        self.test_settings.clear()

        for row, test_name in enumerate(test_names):
            # Получаем сохраненные настройки или значения по умолчанию
            saved_settings = self.current_settings.get(test_name, {})

            is_monitored = saved_settings.get('monitored', False)
            monitor_type = saved_settings.get('monitor_type', 'both')
            ref_lower = saved_settings.get('ref_lower', ref_values.get(test_name, {}).get('ref_lower', 0))
            ref_upper = saved_settings.get('ref_upper', ref_values.get(test_name, {}).get('ref_upper', 0))

            print(f"  {test_name}: monitored={is_monitored}, type={monitor_type}, lower={ref_lower}, upper={ref_upper}")

            # Checkbox мониторинга
            checkbox = QCheckBox()
            checkbox.setChecked(is_monitored)
            checkbox.setStyleSheet("""
                QCheckBox {
                    margin-left: 25px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
            """)

            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout()
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_widget.setLayout(checkbox_layout)

            self.table.setCellWidget(row, 0, checkbox_widget)

            # Название теста
            test_item = QTableWidgetItem(test_name)
            test_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 1, test_item)

            # Комбобокс типа отслеживания
            monitor_type_combo = QComboBox()
            monitor_type_combo.addItem("⬇️ Только нижний", "lower")
            monitor_type_combo.addItem("⬆️ Только верхний", "upper")
            monitor_type_combo.addItem("⬇️⬆️ Оба порога", "both")

            type_index = monitor_type_combo.findData(monitor_type)
            if type_index >= 0:
                monitor_type_combo.setCurrentIndex(type_index)

            monitor_type_combo.setStyleSheet("""
                QComboBox {
                    padding: 3px 5px;
                    border: 1px solid #d5d8dc;
                    border-radius: 3px;
                    background-color: #ffffff;
                    font-size: 11px;
                }
                QComboBox:disabled {
                    background-color: #ecf0f1;
                    color: #95a5a6;
                }
            """)
            self.table.setCellWidget(row, 2, monitor_type_combo)

            # Нижний порог
            lower_spin = QDoubleSpinBox()
            lower_spin.setRange(0, 9999)
            lower_spin.setValue(ref_lower if ref_lower > 0 else 0)
            lower_spin.setDecimals(2)
            lower_spin.setStyleSheet("""
                QDoubleSpinBox {
                    padding: 3px 5px;
                    border: 1px solid #d5d8dc;
                    border-radius: 3px;
                    background-color: #ffffff;
                    font-size: 11px;
                }
                QDoubleSpinBox:disabled {
                    background-color: #ecf0f1;
                    color: #95a5a6;
                }
            """)
            self.table.setCellWidget(row, 3, lower_spin)

            # Верхний порог
            upper_spin = QDoubleSpinBox()
            upper_spin.setRange(0, 9999)
            upper_spin.setValue(ref_upper if ref_upper > 0 else 0)
            upper_spin.setDecimals(2)
            upper_spin.setStyleSheet("""
                QDoubleSpinBox {
                    padding: 3px 5px;
                    border: 1px solid #d5d8dc;
                    border-radius: 3px;
                    background-color: #ffffff;
                    font-size: 11px;
                }
                QDoubleSpinBox:disabled {
                    background-color: #ecf0f1;
                    color: #95a5a6;
                }
            """)
            self.table.setCellWidget(row, 4, upper_spin)

            # Статус
            status_text = self._get_status_text(is_monitored, monitor_type)
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor("#4caf50") if is_monitored else QColor("#95a5a6"))
            self.table.setItem(row, 5, status_item)

            # Описание
            description = self._get_description_text(monitor_type, ref_lower, ref_upper)
            desc_item = QTableWidgetItem(description)
            desc_item.setForeground(QColor("#7f8c8d"))
            self.table.setItem(row, 6, desc_item)

            # Сохраняем виджеты
            self.test_settings[test_name] = {
                'checkbox': checkbox,
                'monitor_type_combo': monitor_type_combo,
                'lower_spin': lower_spin,
                'upper_spin': upper_spin,
                'status_item': status_item,
                'desc_item': desc_item
            }

            # Подключаем сигналы
            checkbox.toggled.connect(
                lambda checked, r=row: self._on_checkbox_toggled(r)
            )

            monitor_type_combo.currentIndexChanged.connect(
                lambda index, r=row: self._on_monitor_type_changed(r)
            )

            # Обновляем доступность порогов
            self._update_thresholds_enabled(row)

            self.table.setRowHeight(row, 45)

    def _get_status_text(self, is_monitored: bool, monitor_type: str) -> str:
        """Получение текста статуса"""
        if not is_monitored:
            return "⏸️ Не активен"
        if monitor_type == 'lower':
            return "✅ Только нижний"
        elif monitor_type == 'upper':
            return "✅ Только верхний"
        else:
            return "✅ Оба порога"

    def _get_description_text(self, monitor_type: str, ref_lower: float, ref_upper: float) -> str:
        """Получение текста описания"""
        if monitor_type == 'lower':
            return f"Критично ниже: {ref_lower}"
        elif monitor_type == 'upper':
            return f"Критично выше: {ref_upper}"
        else:
            return f"Критично: < {ref_lower} или > {ref_upper}"

    def _update_thresholds_enabled(self, row):
        """Обновление доступности порогов"""
        if row < 0 or row >= self.table.rowCount():
            return

        test_item = self.table.item(row, 1)
        if not test_item:
            return

        test_name = test_item.text()
        widgets = self.test_settings.get(test_name)

        if not widgets:
            return

        is_monitored = widgets['checkbox'].isChecked()
        monitor_type = widgets['monitor_type_combo'].currentData()

        # Обновляем доступность
        widgets['monitor_type_combo'].setEnabled(is_monitored)

        if not is_monitored:
            widgets['lower_spin'].setEnabled(False)
            widgets['upper_spin'].setEnabled(False)
        elif monitor_type == 'lower':
            widgets['lower_spin'].setEnabled(True)
            widgets['upper_spin'].setEnabled(False)
        elif monitor_type == 'upper':
            widgets['lower_spin'].setEnabled(False)
            widgets['upper_spin'].setEnabled(True)
        else:  # both
            widgets['lower_spin'].setEnabled(True)
            widgets['upper_spin'].setEnabled(True)

    def _on_checkbox_toggled(self, row):
        """Обработчик переключения checkbox"""
        test_item = self.table.item(row, 1)
        if not test_item:
            return

        test_name = test_item.text()
        widgets = self.test_settings.get(test_name)

        if not widgets:
            return

        is_monitored = widgets['checkbox'].isChecked()

        # Обновляем доступность
        self._update_thresholds_enabled(row)

        # Обновляем статус
        monitor_type = widgets['monitor_type_combo'].currentData()
        widgets['status_item'].setText(self._get_status_text(is_monitored, monitor_type))
        widgets['status_item'].setForeground(QColor("#4caf50") if is_monitored else QColor("#95a5a6"))

    def _on_monitor_type_changed(self, row):
        """Обработчик изменения типа отслеживания"""
        test_item = self.table.item(row, 1)
        if not test_item:
            return

        test_name = test_item.text()
        widgets = self.test_settings.get(test_name)

        if not widgets:
            return

        # Обновляем доступность порогов
        self._update_thresholds_enabled(row)

        # Обновляем статус и описание
        monitor_type = widgets['monitor_type_combo'].currentData()
        is_monitored = widgets['checkbox'].isChecked()

        widgets['status_item'].setText(self._get_status_text(is_monitored, monitor_type))
        widgets['status_item'].setForeground(QColor("#4caf50") if is_monitored else QColor("#95a5a6"))

        ref_lower = widgets['lower_spin'].value()
        ref_upper = widgets['upper_spin'].value()
        widgets['desc_item'].setText(self._get_description_text(monitor_type, ref_lower, ref_upper))

    def select_all_tests(self):
        """Выбрать все тесты"""
        for widgets in self.test_settings.values():
            widgets['checkbox'].setChecked(True)

    def deselect_all_tests(self):
        """Снять выбор со всех тестов"""
        for widgets in self.test_settings.values():
            widgets['checkbox'].setChecked(False)

    def reset_thresholds(self):
        """Сброс порогов к значениям из БД"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Сбросить все пороги к значениям из БД?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        ref_values = self.db_manager.get_test_reference_values()

        for test_name, widgets in self.test_settings.items():
            ref_data = ref_values.get(test_name, {})
            widgets['lower_spin'].setValue(ref_data.get('ref_lower', 0))
            widgets['upper_spin'].setValue(ref_data.get('ref_upper', 0))

            # Обновляем описание
            monitor_type = widgets['monitor_type_combo'].currentData()
            ref_lower = ref_data.get('ref_lower', 0)
            ref_upper = ref_data.get('ref_upper', 0)
            widgets['desc_item'].setText(self._get_description_text(monitor_type, ref_lower, ref_upper))

    def save_settings(self):
        """Сохранение настроек"""
        settings = {}

        for test_name, widgets in self.test_settings.items():
            is_monitored = widgets['checkbox'].isChecked()
            monitor_type = widgets['monitor_type_combo'].currentData()
            ref_lower = widgets['lower_spin'].value()
            ref_upper = widgets['upper_spin'].value()

            # Валидация
            if is_monitored and monitor_type in ['lower', 'both'] and ref_lower <= 0:
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    f"Для теста '{test_name}' укажите нижний порог"
                )
                return

            if is_monitored and monitor_type in ['upper', 'both'] and ref_upper <= 0:
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    f"Для теста '{test_name}' укажите верхний порог"
                )
                return

            if is_monitored and monitor_type == 'both' and ref_lower >= ref_upper:
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    f"Для теста '{test_name}' нижний порог должен быть меньше верхнего"
                )
                return

            settings[test_name] = {
                'monitored': is_monitored,
                'monitor_type': monitor_type,
                'ref_lower': ref_lower,
                'ref_upper': ref_upper
            }

        if self.db_manager.save_test_settings(settings):
            self.settings_saved.emit(settings)
            QMessageBox.information(self, "Успех", "Настройки тестов сохранены")
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось сохранить настройки")

    def get_settings(self) -> dict:
        """Получение настроек"""
        settings = {}
        for test_name, widgets in self.test_settings.items():
            settings[test_name] = {
                'monitored': widgets['checkbox'].isChecked(),
                'monitor_type': widgets['monitor_type_combo'].currentData(),
                'ref_lower': widgets['lower_spin'].value(),
                'ref_upper': widgets['upper_spin'].value()
            }
        return settings