import sqlite3
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


class DatabaseManager:
    def __init__(self, db_path: str = "testbase"):
        self.db_path = db_path
        self.connection = None

    def connect(self) -> bool:
        """Установка соединения с БД"""
        try:
            db_dir = os.path.dirname(self.db_path)

            if not db_dir:
                if hasattr(sys, 'frozen'):
                    import tempfile
                    app_data_dir = os.path.join(os.environ.get('APPDATA', tempfile.gettempdir()), 'CritiCat')
                else:
                    app_data_dir = os.path.dirname(os.path.abspath(__file__))

                os.makedirs(app_data_dir, exist_ok=True)
                self.db_path = os.path.join(app_data_dir, self.db_path)
            else:
                if not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)

                test_file = os.path.join(db_dir, '.write_test')
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                except:
                    import tempfile
                    app_data_dir = os.path.join(os.environ.get('APPDATA', tempfile.gettempdir()), 'CritiCat')
                    os.makedirs(app_data_dir, exist_ok=True)
                    self.db_path = os.path.join(app_data_dir, os.path.basename(self.db_path))

            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=10
            )
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA journal_mode=WAL")

            self._create_tables()
            self._migrate_database()

            return True
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")
            return False

    def _create_tables(self):
        """Создание необходимых таблиц"""
        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS laboratory_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ids INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                department TEXT NOT NULL,
                test_name TEXT NOT NULL,
                result_value REAL,
                ref_upper REAL,
                ref_lower REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS critical_results_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER NOT NULL,
                full_name TEXT,
                ids INTEGER,
                department TEXT,
                test_name TEXT,
                result_value REAL,
                ref_lower REAL,
                ref_upper REAL,
                deviation_percent REAL,
                found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_ignored BOOLEAN DEFAULT 0,
                ignored_at TIMESTAMP,
                UNIQUE(result_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user TEXT DEFAULT 'system',
                action_type TEXT NOT NULL,
                action_description TEXT,
                object_type TEXT,
                object_id TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consent_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                ip_address TEXT,
                consent_version TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL UNIQUE,
                monitored BOOLEAN DEFAULT 0,
                ref_lower REAL,
                ref_upper REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица настроек тестов с типом мониторинга
        cursor.execute("""
               CREATE TABLE IF NOT EXISTS test_settings (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   test_name TEXT NOT NULL UNIQUE,
                   monitored BOOLEAN DEFAULT 0,
                   monitor_type TEXT DEFAULT 'both',
                   ref_lower REAL,
                   ref_upper REAL,
                   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
           """)

        self.connection.commit()

    def _migrate_database(self):
        """Миграция базы данных"""
        try:
            cursor = self.connection.cursor()

            # Проверяем наличие колонки monitor_type
            cursor.execute("PRAGMA table_info(test_settings)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'monitor_type' not in columns:
                cursor.execute("ALTER TABLE test_settings ADD COLUMN monitor_type TEXT DEFAULT 'both'")
                self.connection.commit()
                print("Добавлена колонка monitor_type в test_settings")

        except Exception as e:
            print(f"Ошибка при миграции БД: {e}")

    def _seed_test_data(self):
        """Заполнение тестовыми данными"""
        departments_data = [
            ('Терапевтическое отделение', [
                (1001, 'Иванов Иван Иванович', 'Гемоглобин', 185, 160, 120),
                (1001, 'Иванов Иван Иванович', 'Лейкоциты', 12.5, 9.0, 4.0),
                (1002, 'Петрова Мария Сергеевна', 'Глюкоза', 7.8, 6.1, 3.5),
                (1002, 'Петрова Мария Сергеевна', 'Гемоглобин', 110, 160, 120),
                (1003, 'Сидоров Алексей Петрович', 'СОЭ', 25, 15, 1),
                (1003, 'Сидоров Алексей Петрович', 'Креатинин', 130, 110, 60),
            ]),
            ('Хирургическое отделение', [
                (2001, 'Кузнецова Анна Владимировна', 'Гемоглобин', 95, 160, 120),
                (2001, 'Кузнецова Анна Владимировна', 'Лейкоциты', 15.2, 9.0, 4.0),
                (2002, 'Смирнов Дмитрий Александрович', 'Тромбоциты', 450, 400, 180),
                (2002, 'Смирнов Дмитрий Александрович', 'Билирубин', 25, 21, 5),
            ]),
            ('Кардиологическое отделение', [
                (3001, 'Козлов Михаил Юрьевич', 'Холестерин', 7.2, 5.2, 3.5),
                (3001, 'Козлов Михаил Юрьевич', 'Триглицериды', 2.5, 2.0, 0.5),
                (3002, 'Новикова Ольга Павловна', 'ЛПНП', 4.8, 3.5, 1.5),
                (3002, 'Новикова Ольга Павловна', 'ЛПВП', 0.8, 2.0, 1.0),
            ]),
            ('Неврологическое отделение', [
                (4001, 'Соколова Татьяна Игоревна', 'Глюкоза', 3.0, 6.1, 3.5),
                (4001, 'Соколова Татьяна Игоревна', 'Натрий', 155, 145, 135),
                (4002, 'Лебедев Андрей Владимирович', 'Калий', 6.0, 5.5, 3.5),
            ]),
        ]

        cursor = self.connection.cursor()
        for department, patients in departments_data:
            for ids, full_name, test_name, result_value, ref_upper, ref_lower in patients:
                cursor.execute("""
                    INSERT INTO laboratory_results 
                    (ids, full_name, department, test_name, result_value, ref_upper, ref_lower)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (ids, full_name, department, test_name, result_value, ref_upper, ref_lower))

        self.connection.commit()
        print("Тестовые данные добавлены")

    def disconnect(self):
        """Закрытие соединения"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None

    def is_connected(self) -> bool:
        """Проверка соединения"""
        if self.connection:
            try:
                self.connection.execute("SELECT 1")
                return True
            except:
                return False
        return False

    def get_all_test_names(self) -> List[str]:
        """Получение списка всех уникальных названий тестов"""
        if not self.connection:
            return []
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT DISTINCT test_name FROM laboratory_results ORDER BY test_name")
            return [row['test_name'] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка получения списка тестов: {e}")
            return []

    def get_test_reference_values(self) -> Dict[str, Dict[str, float]]:
        """Получение референсных значений для всех тестов"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT test_name, 
                       MIN(ref_lower) as min_lower, 
                       MAX(ref_upper) as max_upper
                FROM laboratory_results
                WHERE ref_lower IS NOT NULL AND ref_upper IS NOT NULL
                GROUP BY test_name
            """)
            result = {}
            for row in cursor.fetchall():
                result[row['test_name']] = {
                    'ref_lower': row['min_lower'] or 0,
                    'ref_upper': row['max_upper'] or 0
                }
            return result
        except Exception as e:
            print(f"Ошибка получения референсных значений: {e}")
            return {}

    def save_test_settings(self, settings: dict) -> bool:
        """Сохранение настроек тестов"""
        try:
            cursor = self.connection.cursor()

            # Очищаем старые настройки
            cursor.execute("DELETE FROM test_settings")

            # Сохраняем новые
            for test_name, config in settings.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO test_settings 
                    (test_name, monitored, monitor_type, ref_lower, ref_upper, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    test_name,
                    1 if config.get('monitored', False) else 0,
                    config.get('monitor_type', 'both'),
                    config.get('ref_lower', 0),
                    config.get('ref_upper', 0)
                ))

            self.connection.commit()
            return True
        except Exception as e:
            print(f"Ошибка сохранения настроек тестов: {e}")
            return False

    def load_test_settings(self) -> dict:
        """Загрузка настроек тестов"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM test_settings")

            settings = {}
            for row in cursor.fetchall():
                row_dict = dict(row)
                test_name = row_dict['test_name']
                settings[test_name] = {
                    'monitored': bool(row_dict.get('monitored', 0)),
                    'monitor_type': row_dict.get('monitor_type', 'both'),
                    'ref_lower': row_dict.get('ref_lower') or 0,
                    'ref_upper': row_dict.get('ref_upper') or 0
                }

            return settings
        except Exception as e:
            print(f"Ошибка загрузки настроек тестов: {e}")
            return {}

    def get_monitored_tests(self) -> List[str]:
        """Получение списка мониторируемых тестов"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT test_name FROM test_settings 
                WHERE monitored = 1
                ORDER BY test_name
            """)
            return [row['test_name'] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка получения мониторируемых тестов: {e}")
            return []

    def get_pathological_results(self, test_names: List[str],
                                 threshold_percent: float,
                                 excluded_ids: List[int]) -> List[Dict[str, Any]]:
        """Поиск патологических результатов"""
        if not self.connection or not test_names:
            return []

        results = []
        try:
            cursor = self.connection.cursor()
            placeholders = ','.join(['?' for _ in test_names])
            query = f"""
                SELECT * FROM laboratory_results 
                WHERE test_name IN ({placeholders})
                AND ref_lower IS NOT NULL 
                AND ref_upper IS NOT NULL
                AND result_value IS NOT NULL
            """
            params = test_names.copy()

            if excluded_ids:
                excluded_placeholders = ','.join(['?' for _ in excluded_ids])
                query += f" AND id NOT IN ({excluded_placeholders})"
                params.extend(excluded_ids)

            cursor.execute(query, params)

            for row in cursor.fetchall():
                result_dict = dict(row)
                result_value = result_dict['result_value']
                ref_lower = result_dict['ref_lower']
                ref_upper = result_dict['ref_upper']

                if threshold_percent > 0:
                    lower_threshold = ref_lower * (1 - threshold_percent / 100)
                    upper_threshold = ref_upper * (1 + threshold_percent / 100)
                else:
                    lower_threshold = ref_lower
                    upper_threshold = ref_upper

                if result_value < lower_threshold or result_value > upper_threshold:
                    if result_value > ref_upper:
                        deviation = ((result_value - ref_upper) / ref_upper) * 100
                    else:
                        deviation = ((ref_lower - result_value) / ref_lower) * 100
                    result_dict['deviation_percent'] = round(deviation, 2)
                    results.append(result_dict)
        except Exception as e:
            print(f"Ошибка при поиске: {e}")
            raise
        return results

    def get_pathological_results_with_settings(self, test_names: List[str],
                                               threshold_percent: float,
                                               excluded_ids: List[int],
                                               test_settings: dict = None) -> List[Dict[str, Any]]:
        """Поиск патологических результатов с индивидуальными настройками"""
        if not self.connection or not test_names:
            return []

        results = []
        test_settings = test_settings or {}

        try:
            cursor = self.connection.cursor()
            placeholders = ','.join(['?' for _ in test_names])
            query = f"""
                SELECT * FROM laboratory_results 
                WHERE test_name IN ({placeholders})
                AND ref_lower IS NOT NULL 
                AND ref_upper IS NOT NULL
                AND result_value IS NOT NULL
            """
            params = test_names.copy()

            if excluded_ids:
                excluded_placeholders = ','.join(['?' for _ in excluded_ids])
                query += f" AND id NOT IN ({excluded_placeholders})"
                params.extend(excluded_ids)

            cursor.execute(query, params)

            for row in cursor.fetchall():
                result_dict = dict(row)
                result_value = result_dict['result_value']
                test_name = result_dict['test_name']

                # Получаем настройки для теста
                settings = test_settings.get(test_name, {})
                monitor_type = settings.get('monitor_type', 'both')
                ref_lower = settings.get('ref_lower', result_dict['ref_lower'])
                ref_upper = settings.get('ref_upper', result_dict['ref_upper'])

                # Применяем процент отклонения
                if threshold_percent > 0:
                    lower_threshold = ref_lower * (1 - threshold_percent / 100)
                    upper_threshold = ref_upper * (1 + threshold_percent / 100)
                else:
                    lower_threshold = ref_lower
                    upper_threshold = ref_upper

                # Проверяем в зависимости от типа мониторинга
                is_critical = False

                if monitor_type == 'lower':
                    # Только нижний порог
                    if result_value < lower_threshold:
                        is_critical = True
                        deviation = ((ref_lower - result_value) / ref_lower) * 100
                elif monitor_type == 'upper':
                    # Только верхний порог
                    if result_value > upper_threshold:
                        is_critical = True
                        deviation = ((result_value - ref_upper) / ref_upper) * 100
                else:  # both
                    # Оба порога
                    if result_value < lower_threshold:
                        is_critical = True
                        deviation = ((ref_lower - result_value) / ref_lower) * 100
                    elif result_value > upper_threshold:
                        is_critical = True
                        deviation = ((result_value - ref_upper) / ref_upper) * 100

                if is_critical:
                    result_dict['deviation_percent'] = round(deviation, 2)
                    result_dict['monitor_type'] = monitor_type
                    results.append(result_dict)

        except Exception as e:
            print(f"Ошибка при поиске: {e}")
            raise

        return results
    def save_critical_result(self, result: Dict[str, Any]) -> bool:
        """Сохранение критического результата в историю"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO critical_results_history 
                (result_id, full_name, ids, department, test_name, result_value, 
                 ref_lower, ref_upper, deviation_percent, found_at, is_ignored)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 0)
            """, (
                result['id'],
                result.get('full_name', ''),
                result.get('ids', 0),
                result.get('department', 'Не указано'),
                result.get('test_name', ''),
                result.get('result_value', 0),
                result.get('ref_lower', 0),
                result.get('ref_upper', 0),
                result.get('deviation_percent', 0)
            ))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False

    def save_critical_results_batch(self, results: List[Dict[str, Any]]) -> int:
        """Пакетное сохранение критических результатов"""
        saved_count = 0
        for result in results:
            if self.save_critical_result(result):
                saved_count += 1
        return saved_count

    def set_ignored_status(self, result_id: int, is_ignored: bool) -> bool:
        """Установка статуса игнорирования"""
        try:
            cursor = self.connection.cursor()
            if is_ignored:
                cursor.execute("""
                    UPDATE critical_results_history 
                    SET is_ignored = 1, ignored_at = CURRENT_TIMESTAMP
                    WHERE result_id = ?
                """, (result_id,))
            else:
                cursor.execute("""
                    UPDATE critical_results_history 
                    SET is_ignored = 0, ignored_at = NULL
                    WHERE result_id = ?
                """, (result_id,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Ошибка установки статуса: {e}")
            return False

    def set_ignored_status_batch(self, result_ids: List[int], is_ignored: bool) -> int:
        """Пакетная установка статуса"""
        updated_count = 0
        for result_id in result_ids:
            if self.set_ignored_status(result_id, is_ignored):
                updated_count += 1
        return updated_count

    def get_all_critical_results(self, show_ignored: bool = True,
                                 show_active: bool = True) -> List[Dict[str, Any]]:
        """Получение всех критических результатов"""
        try:
            cursor = self.connection.cursor()
            conditions = []
            if show_ignored and not show_active:
                conditions.append("is_ignored = 1")
            elif show_active and not show_ignored:
                conditions.append("is_ignored = 0")

            query = "SELECT * FROM critical_results_history"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY found_at DESC"

            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка получения результатов: {e}")
            return []

    def get_ignored_ids(self) -> List[int]:
        """Получение ID игнорируемых результатов"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT result_id FROM critical_results_history WHERE is_ignored = 1")
            return [row['result_id'] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка получения ID: {e}")
            return []

    def get_statistics(self) -> Dict[str, int]:
        """Получение статистики"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM critical_results_history")
            total = cursor.fetchone()['total']
            cursor.execute("SELECT COUNT(*) as ignored FROM critical_results_history WHERE is_ignored = 1")
            ignored = cursor.fetchone()['ignored']
            return {'total': total, 'ignored': ignored, 'active': total - ignored}
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return {'total': 0, 'ignored': 0, 'active': 0}

    def log_audit(self, action_type: str, action_description: str = "",
                  object_type: str = "", object_id: str = "",
                  details: str = "", user: str = "system") -> bool:
        """Запись в аудит"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO audit_log 
                (timestamp, user, action_type, action_description, object_type, object_id, details)
                VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
            """, (user, action_type, action_description, object_type, object_id, details))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Ошибка записи в аудит: {e}")
            return False

    def get_audit_log(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Получение журнала аудита"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка получения аудита: {e}")
            return []

    def get_audit_statistics(self) -> Dict[str, int]:
        """Получение статистики аудита"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM audit_log")
            total = cursor.fetchone()['total']
            return {'total': total}
        except Exception as e:
            print(f"Ошибка получения статистики аудита: {e}")
            return {'total': 0}

    def clear_audit_log(self) -> bool:
        """Очистка журнала аудита"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM audit_log")
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Ошибка очистки аудита: {e}")
            return False

    def is_result_sent_to_server(self, ids: int, test_name: str, result_value: float) -> bool:
        """Проверка, отправлен ли результат на VDS"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count FROM critical_results_history 
                WHERE ids = ? AND test_name = ? AND result_value = ?
                AND sent_to_server = 1
            """, (ids, test_name, result_value))
            row = cursor.fetchone()
            return row['count'] > 0 if row else False
        except:
            return False

    def mark_as_sent_to_server(self, result_id: int):
        """Пометка результата как отправленного на VDS"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE critical_results_history 
                SET sent_to_server = 1 
                WHERE result_id = ?
            """, (result_id,))
            self.connection.commit()
            return True
        except:
            return False