from typing import List, Dict

from PySide6.QtWidgets import (QMainWindow, QTabWidget, QStatusBar,
                               QMessageBox, QVBoxLayout, QWidget, QPushButton)
from PySide6.QtCore import Qt, QTimer
from ui.monitor_tab import MonitorTab
from ui.settings_tab import SettingsTab
from ui.history_tab import HistoryTab
from ui.telegram_tab import TelegramTab
from ui.audit_tab import AuditTab
from worker import CheckWorker
from database import DatabaseManager
from models import Settings
from server_client import ServerClient



class MainWindow(QMainWindow):
    def __init__(self, theme_controller=None, app_settings=None):
        super().__init__()
        self.settings = Settings()
        self.db_manager = DatabaseManager()
        self.check_worker = None
        self.timer = None
        self.excluded_ids = set()
        self.is_checking = False

        # VDS Server
        self.server_client = ServerClient()
        self.server_settings = {
            'url': '',
            'api_key': '',
            'enabled': False,
            'poll_interval': 30
        }

        # Регистрируем callback
        self.server_client.register_callback(self._on_server_confirmation)

        # Управление диалогами
        self.current_alert_dialog = None

        # Темы
        self.theme_controller = theme_controller
        self.app_settings = app_settings

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Мониторинг лабораторных исследований")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("QMainWindow { background-color: #f0f2f5; }")

        self.theme_btn = QPushButton()
        self.theme_btn.setMaximumHeight(25)
        self.theme_btn.clicked.connect(self._toggle_theme)

        self.tab_widget = QTabWidget()
        self.monitor_tab = MonitorTab(self)
        self.history_tab = HistoryTab(self)
        self.telegram_tab = TelegramTab(self)
        self.settings_tab = SettingsTab(self)
        self.audit_tab = AuditTab(self)

        self.tab_widget.addTab(self.monitor_tab, "🔍 Мониторинг")
        self.tab_widget.addTab(self.history_tab, "📋 История")
        self.tab_widget.addTab(self.telegram_tab, "📱 Уведомления")
        self.tab_widget.addTab(self.settings_tab, "⚙️ Настройки")
        self.tab_widget.addTab(self.audit_tab, "🔐 Аудит")

        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.history_tab.ignore_toggled.connect(self._on_ignore_toggled)

        self.setCentralWidget(self.tab_widget)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")
        self.status_bar.addPermanentWidget(self.theme_btn)

        self._update_theme_button_text()
        self.apply_settings()

    # ========== VDS СЕРВЕР ==========

    def _on_server_confirmation(self, confirmations):
        """Обработка подтверждений с VDS"""
        for confirmation in confirmations:
            # Проверяем, что confirmation - словарь
            if not isinstance(confirmation, dict):
                self.log_message(f"Неожиданный формат: {type(confirmation)}")
                continue

            ids = confirmation.get('ids')
            test_name = confirmation.get('test_name')
            result_key = confirmation.get('result_key')

            if ids and test_name:
                self.log_message(f"✅ Подтверждено с VDS: IDS={ids}, {test_name}")
                self._mark_result_as_confirmed(ids, test_name)
            else:
                self.log_message(f"Нет данных в подтверждении: {confirmation}")
    def _mark_result_as_confirmed(self, ids: int, test_name: str):
        """Помечает результат в игнор"""
        if not self.db_manager.is_connected():
            return
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("""
                SELECT result_id FROM critical_results_history 
                WHERE ids = ? AND test_name = ? AND is_ignored = 0
                ORDER BY found_at DESC LIMIT 1
            """, (ids, test_name))
            row = cursor.fetchone()
            if row:
                result_id = row['result_id']
                self.db_manager.set_ignored_status(result_id, True)
                self.excluded_ids.add(result_id)
                self.monitor_tab.update_excluded_count(len(self.excluded_ids))
                self.log_message(f"   ID:{result_id} помечен в игнор")
        except Exception as e:
            self.log_message(f"   Ошибка: {e}")

    def save_server_settings(self):
        """Сохранение настроек VDS с проверкой авторизации"""
        try:
            # Получаем настройки
            url = self.telegram_tab.server_url_input.text().strip()
            api_key = self.telegram_tab.api_key_input.text().strip()
            enabled = self.telegram_tab.server_enabled_cb.isChecked()
            interval = self.telegram_tab.poll_interval_spin.value()

            # Сохраняем
            self.server_settings['url'] = url
            self.server_settings['api_key'] = api_key
            self.server_settings['enabled'] = enabled
            self.server_settings['poll_interval'] = interval

            # Обновляем клиент
            self.server_client.set_server_url(url)
            self.server_client.set_api_key(api_key)

            # Проверяем авторизацию если включено
            if enabled and url and api_key:
                success, message = self.server_client.verify_auth()
                if success:
                    self.log_message(f"✅ Авторизация VDS: {message}")
                    # Запускаем polling
                    self.server_client.start_polling(interval)
                    self.log_message(f"✅ Опрос VDS запущен ({interval}с)")
                else:
                    self.log_message(f"❌ Ошибка авторизации: {message}")
                    self.server_client.stop_polling()
            else:
                self.server_client.stop_polling()
                if not api_key:
                    self.log_message("⚠️ API ключ не указан")

        except Exception as e:
            self.log_message(f"❌ Ошибка: {e}")

    def send_results_to_server(self, results) -> bool:
        """Отправка результатов на VDS (с проверкой дубликатов)"""
        if not self.server_settings.get('enabled'):
            return False

        if not self.server_client.is_configured():
            return False

        try:
            # Подготавливаем данные
            prepared = []
            for r in results:
                prepared.append({
                    'ids': int(r.get('ids', 0) or 0),
                    'department': str(r.get('department', 'Не указано')),
                    'test_name': str(r.get('test_name', 'Неизвестный тест')),
                    'result_value': float(r.get('result_value', 0) or 0),
                    'ref_lower': float(r['ref_lower']) if r.get('ref_lower') else 0,
                    'ref_upper': float(r['ref_upper']) if r.get('ref_upper') else 0,
                    'deviation_percent': float(r['deviation_percent']) if r.get('deviation_percent') else 0,
                    'monitor_type': str(r.get('monitor_type', 'both')),
                })

            response = self.server_client.send_results(prepared)

            sent = response.get('sent_count', 0)
            skipped = response.get('skipped_count', 0)
            failed = response.get('failed_count', 0)

            if response.get('success'):
                self.log_message(f"✅ VDS: отправлено {sent}, пропущено {skipped}, ошибок {failed}")
                return True
            else:
                self.log_message(f"❌ VDS: {response.get('message', '')}")
                return False

        except Exception as e:
            self.log_message(f"❌ Исключение: {e}")
            return False


    def _update_theme_button_text(self):
        if self._get_current_theme() == 'dark':
            self.theme_btn.setText("☀️ Светлая тема")
        else:
            self.theme_btn.setText("🌙 Темная тема")

    def _get_current_theme(self):
        if self.theme_controller:
            try:
                return self.theme_controller.get_current_theme()
            except:
                pass
        return 'light'

    def _toggle_theme(self):
        if self.theme_controller:
            try:
                new_theme = self.theme_controller.toggle_theme()
                if self.app_settings:
                    self.app_settings.setValue('theme', new_theme)
                self._update_theme_button_text()
                self.log_message(f"Тема: {'темная' if new_theme == 'dark' else 'светлая'}")
            except Exception as e:
                self.log_message(f"Ошибка темы: {e}")

    def _on_tab_changed(self, index):
        widget = self.tab_widget.widget(index)
        if widget == self.history_tab:
            self.history_tab.refresh_data()
        elif widget == self.audit_tab:
            self.audit_tab.refresh_data()

    def _on_ignore_toggled(self, result_id, is_ignored):
        if is_ignored:
            self.excluded_ids.add(result_id)
        else:
            self.excluded_ids.discard(result_id)
        self.monitor_tab.update_excluded_count(len(self.excluded_ids))

    def log_message(self, message: str):
        self.monitor_tab.add_log_message(message)

    def log_audit(self, action_type, action_description="", object_type="", object_id="", details=""):
        if self.db_manager.is_connected():
            self.db_manager.log_audit(action_type, action_description, object_type, object_id, details)

    def apply_settings(self):
        new_settings = self.settings_tab.get_settings()
        self.settings = new_settings
        self.db_manager.disconnect()
        if self.db_manager.connect():
            self.status_bar.showMessage("✓ Подключено к БД")
            self.log_message("Соединение с БД установлено")
            self.test_settings = self.db_manager.load_test_settings()
            monitored_tests = [n for n, c in self.test_settings.items() if c.get('monitored')]
            self.settings.monitored_tests = monitored_tests
            self.excluded_ids = set(self.db_manager.get_ignored_ids())
            self.monitor_tab.update_excluded_count(len(self.excluded_ids))
            if monitored_tests:
                self.log_message(f"Мониторируемых тестов: {len(monitored_tests)}")
        else:
            self.status_bar.showMessage("✗ Ошибка подключения к БД")
            self.log_message("Ошибка подключения к БД")
        self.restart_check_timer()

    def restart_check_timer(self):
        if self.timer:
            self.timer.stop()
        self.timer = QTimer()
        self.timer.timeout.connect(self.start_check)
        self.timer.start(self.settings.check_interval * 60 * 1000)
        self.log_message(f"Таймер: {self.settings.check_interval} мин")

    def start_check(self):
        if self.is_checking:
            return
        if not self.db_manager.is_connected():
            return
        if not self.settings.monitored_tests:
            self.log_message("Нет тестов для мониторинга")
            return

        self.is_checking = True
        self.monitor_tab.manual_check_btn.setEnabled(False)

        self.test_settings = self.db_manager.load_test_settings()

        self.check_worker = CheckWorker(
            self.settings.db_path,
            self.settings.monitored_tests,
            0,
            list(self.excluded_ids),
            self.test_settings
        )
        self.check_worker.finished.connect(self.on_check_finished)
        self.check_worker.error_occurred.connect(self.on_check_error)
        self.check_worker.start()
        self.log_message("Проверка запущена")

    def on_check_error(self, error_message):
        self.log_message(f"Ошибка: {error_message}")
        self.is_checking = False
        self.monitor_tab.manual_check_btn.setEnabled(True)

    def on_check_finished(self, results):
        """Обработка результатов проверки"""
        self.is_checking = False
        self.monitor_tab.manual_check_btn.setEnabled(True)
        self.status_bar.showMessage("✓ Проверка завершена")

        if results:
            # Сохраняем в БД
            try:
                self.db_manager.save_critical_results_batch(results)
            except Exception as e:
                self.log_message(f"Ошибка сохранения: {e}")

            # Фильтруем
            filtered = []
            for r in results:
                try:
                    if r.get('id') not in self.excluded_ids:
                        filtered.append(r)
                except:
                    filtered.append(r)

            if filtered:
                self.log_message(f"Критических: {len(filtered)}")

                # Отправка на VDS
                if self.server_settings.get('enabled'):
                    try:
                        # Подготавливаем данные
                        prepared = self._prepare_results_for_server(filtered)
                        if prepared:
                            self.send_results_to_server(prepared)
                    except Exception as e:
                        self.log_message(f"❌ Ошибка VDS: {e}")

                # Показ диалога
                try:
                    self.show_alerts_dialog(filtered)
                except Exception as e:
                    self.log_message(f"Ошибка диалога: {e}")
            else:
                self.log_message("Все результаты уже в игноре")
        else:
            self.log_message("Отклонений не найдено")

        try:
            if self.tab_widget.currentWidget() == self.history_tab:
                self.history_tab.refresh_data()
        except:
            pass


    def show_alerts_dialog(self, results):
        from ui.alert_dialog import AlertDialog
        self._close_current_alert_dialog()
        dialog = AlertDialog(results, self)
        self.current_alert_dialog = dialog
        dialog.finished.connect(self._on_alert_dialog_finished)
        if dialog.exec() == AlertDialog.Accepted:
            ignored_ids = dialog.get_ignored_ids()
            for rid in ignored_ids:
                self.excluded_ids.add(rid)
            self.db_manager.set_ignored_status_batch(ignored_ids, True)
            if ignored_ids:
                self.log_message(f"Игнорировано: {len(ignored_ids)}")
        self.monitor_tab.update_excluded_count(len(self.excluded_ids))

    def _close_current_alert_dialog(self):
        if self.current_alert_dialog and self.current_alert_dialog.isVisible():
            try:
                self.current_alert_dialog.finished.disconnect(self._on_alert_dialog_finished)
            except:
                pass
            self.current_alert_dialog.reject()
            self.current_alert_dialog = None

    def _on_alert_dialog_finished(self, result_code):
        self.current_alert_dialog = None

    def closeEvent(self, event):
        self._close_current_alert_dialog()
        self.server_client.stop_polling()
        if self.timer:
            self.timer.stop()
        self.db_manager.disconnect()
        event.accept()


    def _prepare_results_for_server(self, results: List[Dict]) -> List[Dict]:
        """Подготовка результатов для отправки на VDS"""
        prepared = []

        for r in results:
            try:
                prepared.append({
                    'ids': int(r.get('ids', 0) or 0),
                    'department': str(r.get('department', 'Не указано')),
                    'test_name': str(r.get('test_name', 'Неизвестный тест')),
                    'result_value': float(r.get('result_value', 0) or 0),
                    'ref_lower': float(r['ref_lower']) if r.get('ref_lower') is not None else None,
                    'ref_upper': float(r['ref_upper']) if r.get('ref_upper') is not None else None,
                    'deviation_percent': float(r['deviation_percent']) if r.get('deviation_percent') is not None else None,
                    'monitor_type': str(r.get('monitor_type', 'both')),
                })
            except Exception as e:
                self.log_message(f"Ошибка подготовки: {e}")
                continue

        return prepared