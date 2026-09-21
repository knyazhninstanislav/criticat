import sqlite3
import os
from typing import List, Dict, Any
from .base import LisProvider, LisResult


class MockLisProvider(LisProvider):
    """
    Мок-провайдер ЛИС.

    Использует локальную SQLite с таблицей laboratory_results.
    Это твоя текущая 'моковая БД ЛИС' — заглушка для разработки.
    """

    def __init__(self, db_path: str = "mock_lis.db"):
        self.db_path = db_path
        self.connection = None

    def connect(self) -> bool:
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row

            # Создаём таблицу, если её нет
            self.connection.execute("""
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
            self.connection.commit()
            return True
        except Exception as e:
            print(f"MockLis: ошибка подключения: {e}")
            return False

    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    def is_connected(self) -> bool:
        if not self.connection:
            return False
        try:
            self.connection.execute("SELECT 1")
            return True
        except:
            return False

    def get_all_test_names(self) -> List[str]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT DISTINCT test_name FROM laboratory_results ORDER BY test_name")
        return [row['test_name'] for row in cursor.fetchall()]

    def get_test_reference_values(self) -> Dict[str, Dict[str, float]]:
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT test_name,
                   MIN(ref_lower) as min_lower,
                   MAX(ref_upper) as max_upper
            FROM laboratory_results
            WHERE ref_lower IS NOT NULL AND ref_upper IS NOT NULL
            GROUP BY test_name
        """)
        return {
            row['test_name']: {
                'ref_lower': row['min_lower'] or 0,
                'ref_upper': row['max_upper'] or 0
            }
            for row in cursor.fetchall()
        }

    def get_results_for_tests(
        self,
        test_names: List[str],
        excluded_ids: List[int]
    ) -> List[LisResult]:
        if not self.connection or not test_names:
            return []

        cursor = self.connection.cursor()
        placeholders = ','.join(['?' for _ in test_names])
        query = f"""
            SELECT * FROM laboratory_results
            WHERE test_name IN ({placeholders})
            AND ref_lower IS NOT NULL
            AND ref_upper IS NOT NULL
            AND result_value IS NOT NULL
        """
        params = list(test_names)

        if excluded_ids:
            excluded_placeholders = ','.join(['?' for _ in excluded_ids])
            query += f" AND id NOT IN ({excluded_placeholders})"
            params.extend(excluded_ids)

        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            results.append(LisResult(
                id=row['id'],
                ids=row['ids'],
                full_name=row['full_name'],
                department=row['department'],
                test_name=row['test_name'],
                result_value=row['result_value'],
                ref_lower=row['ref_lower'],
                ref_upper=row['ref_upper'],
            ))
        return results

    # lis/mock_provider.py
    def seed_demo_data(self, force: bool = False) -> int:
        """
        Заполнить мок-ЛИС тестовыми данными.
        Автоматически подключается, если нет соединения.
        """
        print("[MockLis] ====== SEED START ======")

        # Автоподключение
        if not self.connection:
            print("[MockLis] Нет соединения, подключаюсь...")
            if not self.connect():
                print("[MockLis] ❌ Не удалось подключиться")
                return 0

        print(f"[MockLis] Файл БД: {self.db_path}")

        cursor = self.connection.cursor()

        # Проверяем схему
        cursor.execute("PRAGMA table_info(laboratory_results)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"[MockLis] Колонки таблицы: {columns}")

        # Проверяем текущее количество
        cursor.execute("SELECT COUNT(*) as cnt FROM laboratory_results")
        count = cursor.fetchone()['cnt']
        print(f"[MockLis] Записей сейчас: {count}")

        if not force and count > 0:
            print(f"[MockLis] Данные уже есть ({count}), пропускаю. Используй force=True для перезалива.")
            return 0

        if force:
            cursor.execute("DELETE FROM laboratory_results")
            self.connection.commit()
            print("[MockLis] Таблица очищена")

        # === ДАННЫЕ ===
        # Формат: (ids, full_name, test_name, result_value, ref_upper, ref_lower)
        demo_data = [
            # Терапевтическое
            (1001, 'Иванов Иван Иванович', 'Гемоглобин', 185.0, 160.0, 120.0),
            (1001, 'Иванов Иван Иванович', 'Лейкоциты', 12.5, 9.0, 4.0),
            (1001, 'Иванов Иван Иванович', 'СОЭ', 25.0, 15.0, 1.0),
            (1002, 'Петрова Мария Сергеевна', 'Глюкоза', 7.8, 6.1, 3.5),
            (1002, 'Петрова Мария Сергеевна', 'Гемоглобин', 110.0, 160.0, 120.0),
            (1002, 'Петрова Мария Сергеевна', 'Креатинин', 130.0, 110.0, 60.0),
            (1003, 'Сидоров Алексей Петрович', 'СОЭ', 25.0, 15.0, 1.0),
            (1003, 'Сидоров Алексей Петрович', 'Креатинин', 130.0, 110.0, 60.0),
            (1003, 'Сидоров Алексей Петрович', 'Глюкоза', 6.5, 6.1, 3.5),

            # Хирургическое
            (2001, 'Кузнецова Анна Владимировна', 'Гемоглобин', 95.0, 160.0, 120.0),
            (2001, 'Кузнецова Анна Владимировна', 'Лейкоциты', 15.2, 9.0, 4.0),
            (2001, 'Кузнецова Анна Владимировна', 'Тромбоциты', 450.0, 400.0, 180.0),
            (2002, 'Смирнов Дмитрий Александрович', 'Тромбоциты', 450.0, 400.0, 180.0),
            (2002, 'Смирнов Дмитрий Александрович', 'Билирубин', 25.0, 21.0, 5.0),
            (2002, 'Смирнов Дмитрий Александрович', 'АЛТ', 55.0, 40.0, 10.0),

            # Кардиологическое
            (3001, 'Козлов Михаил Юрьевич', 'Холестерин', 7.2, 5.2, 3.5),
            (3001, 'Козлов Михаил Юрьевич', 'Триглицериды', 2.5, 2.0, 0.5),
            (3001, 'Козлов Михаил Юрьевич', 'Тропонин I', 2.5, 0.04, 0.0),
            (3002, 'Новикова Ольга Павловна', 'ЛПНП', 4.8, 3.5, 1.5),
            (3002, 'Новикова Ольга Павловна', 'ЛПВП', 0.8, 2.0, 1.0),
            (3002, 'Новикова Ольга Павловна', 'Холестерин', 6.8, 5.2, 3.5),
            (3003, 'Морозов Сергей Николаевич', 'Тропонин I', 5.0, 0.04, 0.0),
            (3003, 'Морозов Сергей Николаевич', 'КФК-МВ', 45.0, 25.0, 0.0),

            # Неврологическое
            (4001, 'Соколова Татьяна Игоревна', 'Глюкоза', 3.0, 6.1, 3.5),
            (4001, 'Соколова Татьяна Игоревна', 'Натрий', 155.0, 145.0, 135.0),
            (4001, 'Соколова Татьяна Игоревна', 'Калий', 6.0, 5.5, 3.5),
            (4002, 'Лебедев Андрей Владимирович', 'Калий', 6.0, 5.5, 3.5),
            (4002, 'Лебедев Андрей Владимирович', 'Натрий', 130.0, 145.0, 135.0),
            (4002, 'Лебедев Андрей Владимирович', 'Глюкоза', 8.5, 6.1, 3.5),

            # Реанимационное
            (5001, 'Волков Дмитрий Андреевич', 'Тропонин I', 8.0, 0.04, 0.0),
            (5001, 'Волков Дмитрий Андреевич', 'Калий', 7.5, 5.5, 3.5),
            (5001, 'Волков Дмитрий Андреевич', 'Глюкоза', 2.5, 6.1, 3.5),
            (5002, 'Зайцева Елена Викторовна', 'Гемоглобин', 70.0, 160.0, 120.0),
            (5002, 'Зайцева Елена Викторовна', 'Тромбоциты', 100.0, 400.0, 180.0),
            (5002, 'Зайцева Елена Викторовна', 'Лейкоциты', 25.0, 9.0, 4.0),
        ]

        # Отделения (отдельный список, чтобы не тащить в кортеж)
        patient_departments = {
            1001: 'Терапевтическое отделение',
            1002: 'Терапевтическое отделение',
            1003: 'Терапевтическое отделение',
            2001: 'Хирургическое отделение',
            2002: 'Хирургическое отделение',
            3001: 'Кардиологическое отделение',
            3002: 'Кардиологическое отделение',
            3003: 'Кардиологическое отделение',
            4001: 'Неврологическое отделение',
            4002: 'Неврологическое отделение',
            5001: 'Реанимационное отделение',
            5002: 'Реанимационное отделение',
        }

        added = 0
        errors = 0

        for row in demo_data:
            ids, full_name, test_name, result_value, ref_upper, ref_lower = row
            department = patient_departments.get(ids, 'Не указано')

            try:
                cursor.execute("""
                    INSERT INTO laboratory_results
                    (ids, full_name, department, test_name, result_value, ref_upper, ref_lower)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (ids, full_name, department, test_name, result_value, ref_upper, ref_lower))
                added += 1
            except Exception as e:
                errors += 1
                print(f"[MockLis] ❌ INSERT {full_name}/{test_name}: {e}")

        self.connection.commit()

        # Проверка
        cursor.execute("SELECT COUNT(*) as cnt FROM laboratory_results")
        final_count = cursor.fetchone()['cnt']

        print(f"[MockLis] ✅ Добавлено: {added}, ошибок: {errors}, всего в БД: {final_count}")
        print("[MockLis] ====== SEED END ======")

        return added