# 🖥️ CritiCat Desktop

Десктопный модуль системы **CritiCat** - приложение на PySide6 для мониторинга критических значений лабораторных исследований в реальном времени. Работает с ЛИС (реальной или моковой), анализатором **Swelab Alfa** через COM-порт и VDS-сервером для отправки уведомлений.

---

## 📋 Содержание

- [Что это](#что-это)
- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Структура проекта](#структура-проекта)
- [Установка](#установка)
- [Запуск](#запуск)
- [Провайдеры ЛИС](#провайдеры-лис)
- [Анализатор Swelab Alfa](#анализатор-swelab-alfa)
- [VDS-сервер](#vds-сервер)
- [Настройка](#настройка)
- [Сборка](#сборка)
- [Тестирование](#тестирование)
- [Логотип](#логотип)
- [FAQ](#faq)

---

## 🎯 Что это

CritiCat Desktop - это **толстый клиент** для лаборатории, который:

1. Периодически опрашивает ЛИС (или читает данные с анализатора Swelab Alfa).
2. Фильтрует результаты по настроенным критическим порогам.
3. Показывает всплывающее окно с критическими отклонениями.
4. Даёт возможность игнорировать отдельные результаты или целые группы.
5. Ведёт историю всех критических результатов.
6. Отправляет уведомления на VDS-сервер (систему оповещения для врачей).
7. Логирует все действия в журнал аудита.

---

## ✨ Возможности

### 🔍 Мониторинг

- Периодическая проверка ЛИС с настраиваемым интервалом.
- Ручной запуск проверки кнопкой «ПРОВЕРИТЬ».
- Настраиваемые тесты и пороги (только нижний, только верхний, оба).
- Настройка типа мониторинга для каждого теста отдельно.

### 📋 История

- Полная история критических результатов с фильтрами.
- Фильтры: Все / Активные / Игнорируемые.
- Поиск по ФИО, IDS, отделению, названию теста.
- Фильтр по диапазону дат с быстрыми пресетами (сегодня, неделя, месяц).
- Массовое игнорирование и снятие игнора.

### 🔐 Аудит

- Журнал всех действий пользователя.
- Фильтр по типу действия и датам.
- Отдельные типы действий для VDS-операций.
- Очистка журнала аудита.

### 🖥️ VDS-админка

- Управление пользователями (Добавление, редактирование, активация/деактивация, удаление).
- Статистика по результатам и пользователям.
- Проверка авторизации по API-ключу.

### 🎨 Темизация

- Светлая и тёмная темы.
- Переключение на лету.
- Сохранение выбора в `QSettings`.

### 🩸 Swelab Alfa (BM800)

- Приём результатов напрямую с гематологического анализатора.
- Чтение XML-потока с RS-232 (COM-порт).
- Фильтрация фоновых проб (`AUTOBACKGROUND`).
- Совместимость с интерфейсом `BaseProvider`.

---

## 🏗️ Архитектура

Схема потоков данных:

- **UI Layer** (PySide6) — окна, вкладки, диалоги.
- **Service Layer** (`services/critical_filter.py`) — логика критичности.
- **Provider Layer** (`providers/`) — абстракция над ЛИС: Mock, Swelab.
- **Database Layer** (`database/database.py`) — своя SQLite-БД (WAL).
- **Server Client** (`services/server_client.py`) — HTTP-клиент для VDS.
- **Worker** (`database/worker.py`) — фоновый поток проверки ЛИС.

Поток данных:

`ЛИС → Provider → CriticalFilter → DatabaseManager → UI → ServerClient (VDS)`

### Ключевые слои

| Слой | Файлы | Ответственность |
|------|-------|-----------------|
| **UI** | `ui/` | Окна, вкладки, диалоги, темы, логотип |
| **Services** | `services/critical_filter.py` | Логика определения критичности |
| **Providers** | `providers/` | Абстракция над ЛИС (Mock, Swelab) |
| **Database** | `database/` | Своя SQLite-БД, аудит, настройки |
| **Server** | `services/server_client.py` | HTTP-клиент для VDS |
| **Worker** | `database/worker.py` | Фоновый поток проверки ЛИС |

---

## 📂 Структура проекта

```
desktop/
├── main.py                      # Точка входа
├── version.py                   # Версия приложения
├── setup.py                     # Установка как пакет
├── build.py                     # Сборка exe + installer
├── installer.iss                # Inno Setup скрипт
│
├── ui/
│   ├── main_window.py           # Главное окно (QMainWindow)
│   ├── themes.py                # Светлая/тёмная темы
│   ├── styles.py                # Общие стили
│   ├── criti_cat_logo.py        # Отрисовка логотипа
│   ├── splash_screen.py         # Splash screen с анимацией
│   ├── tabs/
│   │   ├── monitor_tab.py       # Вкладка мониторинга
│   │   ├── history_tab.py       # История результатов
│   │   ├── settings_tab.py      # Настройки
│   │   ├── audit_tab.py         # Журнал аудита
│   │   └── vds_admin_tab.py     # VDS-админка
│   ├── dialogs/
│   │   ├── alert_dialog.py      # Окно критических значений
│   │   └── test_settings_dialog.py  # Настройка тестов
│   └── widgets/
│       └── search_widget.py     # Поиск с фильтром дат
│
├── providers/
│   ├── base.py                  # BaseProvider, BaseResult
│   ├── factory.py               # ProviderFactory
│   ├── mock_lis_provider.py     # Моковая ЛИС (SQLite)
│   └── swelab_com_provider.py   # Swelab Alfa через COM
│
├── database/
│   ├── database.py              # DatabaseManager (своя БД)
│   ├── models.py                # Settings, LabResult
│   └── worker.py                # CheckWorker (QThread)
│
├── services/
│   ├── critical_filter.py       # Логика критичности
│   └── server_client.py         # HTTP-клиент VDS
│
├── db/
│   ├── criticat.db              # Своя БД (создаётся автоматически)
│   └── mock_lis.db              # Моковая ЛИС (создаётся при seed)
│
└── tests/
    ├── test_swelab_com_provider.py
    └── test_swelab_from_file.py
```

---

## 🚀 Установка

### Требования

- Python **3.8+**
- Windows / Linux / macOS

### Зависимости

Установка всех зависимостей одной командой:

`pip install -r requirements.txt`

Или вручную:

`pip install PySide6>=6.5.0`

`pip install requests>=2.28.0`

`pip install cryptography>=41.0.0`

`pip install Pillow>=10.0.0`

`pip install pyserial>=3.5`

Последний пакет (`pyserial`) нужен только для работы с Swelab.

### Установка как пакет

`pip install -e .`

---

## ▶️ Запуск

`python main.py`

Или через entry point:

`criticat`

При запуске:

1. Показывается splash screen с логотипом CritiCat (2-5 секунд).
2. Инициализируется тема из `QSettings`.
3. Подключается БД CritiCat.
4. Создаётся провайдер ЛИС (mock или swelab).
5. Открывается главное окно.

---

## 🔌 Провайдеры ЛИС

### Mock-провайдер (`mock`)

Заглушка на SQLite. Создаёт `db/mock_lis.db` с таблицей `laboratory_results`. При первом запуске заливает демо-данные (12 пациентов, 5 отделений, ~36 результатов).

Создание:

`from providers.factory import ProviderFactory`

`lis = ProviderFactory.create(provider_type='mock', db_path='./db/mock_lis.db')`

`lis.connect()`

`lis.seed_demo_data()`

Демо-данные включают:

- Терапевтическое отделение (Иванов, Петрова, Сидоров)
- Хирургическое (Кузнецова, Смирнов)
- Кардиологическое (Козлов, Новикова, Морозов)
- Неврологическое (Соколова, Лебедев)
- Реанимационное (Волков, Зайцева)

### Swelab COM (`swelab_com`)

Реальный анализатор **Swelab Alfa (BM800)** через RS-232.

Создание:

`lis = ProviderFactory.create(provider_type='swelab_com', port='COM3', baudrate=19200, skip_background=True)`

`lis.connect()`

---

## 🩸 Анализатор Swelab Alfa

### Как работает

1. Прибор после каждого анализа **сам** шлёт XML в COM-порт (запрос не нужен).
2. `SwelabComProvider` открывает порт, читает в фоновом потоке.
3. Собирает `<sample>...</sample>` из возможных «осколков».
4. Парсит XML, превращает каждый параметр в `BaseResult`.
5. Результаты попадают в потокобезопасную очередь.

### Что умеет провайдер

- 🔌 RS-232 / COM-порт через `pyserial` (19200 8N1).
- 🧵 Фоновое чтение — GUI не блокируется.
- 🧩 Склейка разорванных сообщений — XML может прийти частями.
- 🚫 Фильтрация фона — `AUTOBACKGROUND` (программа `BACKGROUND`) отбрасывается.
- 📚 Кэш референсов — границы нормы накапливаются.
- 🎯 Совместимость с `BaseProvider` — тот же интерфейс, что у Mock.

### Поддерживаемые параметры

| Группа | Параметры |
|--------|-----------|
| Эритроциты | RBC, MCV, HCT, MCH, MCHC, RDWR, RDWA |
| Тромбоциты | PLT, MPV, PCT, PDW, LPCR |
| Гемоглобин | HGB |
| Лейкоциты | WBC, LA, MA, GA, LR, MR, GR |

### Быстрый старт

`from providers.factory import ProviderFactory`

`lis = ProviderFactory.create('swelab_com', port='COM3', baudrate=19200, skip_background=True)`

`if lis.connect():`

`    lis.disconnect()`

### Тесты

`pytest tests/test_swelab_com_provider.py -v`

`pytest tests/test_swelab_from_file.py -v`

Для интеграционного теста нужен виртуальный COM-порт:

- **Windows** — [com0com](https://sourceforge.net/projects/com0com/)
- **Linux/macOS** — `socat`

---

## 🖥️ VDS-сервер

CritiCat Desktop может отправлять критические результаты на удалённый VDS-сервер для уведомлений врачам.

### Возможности клиента

- Авторизация по API-ключу (`X-API-Key` + `Authorization: Bearer`).
- Проверка соединения перед запросами.
- Отправка результатов пакетом с защитой от дублей.
- Опрос подтверждений от врачей.
- Управление пользователями.

### Настройка в UI

Вкладка «⚙️ Настройки → Настройки VDS сервера»:

| Поле | Описание                           |
|------|------------------------------------|
| Включить отправку | Чекбокс активации                  |
| URL сервера | Например, `http://127.0.0.1:26000` |
| API ключ | Секретный ключ                     |
| Интервал опроса | 10–300 секунд                      |

### Программный вызов

`from services.server_client import ServerClient`

`client = ServerClient(url="http://...", api_key="...")`

`ok, msg = client.verify_auth()`

Далее через `client.send_results([...])` передаётся список словарей с полями `ids`, `department`, `test_name`, `result_value`, `ref_lower`, `ref_upper`, `deviation_percent`, `monitor_type`.

---

## ⚙️ Настройка

### Вкладка «Настройки»

1. Периодичность проверки - 1–60 минут.
2. Настроить отслеживаемые тесты - открывает диалог выбора:
   - Чекбокс мониторинга
   - Тип: только нижний / только верхний / оба порога
   - Нижний и верхний пороги
   - Живое описание: «Критично: < X или > Y»
3. Тема оформления — светлая / тёмная.
4. Настройки VDS — URL, API-ключ, интервал опроса.

### QSettings

Приложение хранит в `QSettings('CritiCat', 'LabMonitor')`:

- `theme` — `light` / `dark`
- `lis_provider` — `mock` / `swelab_com`
- `lis_db_path` — путь к БД ЛИС

---

## 📦 Сборка

### Сборка exe (Windows)

`python build.py`

Что делает скрипт:

1. Очищает `build/`, `dist/`, `__pycache__`, `.spec`.
2. Устанавливает зависимости.
3. Собирает `dist/CritiCat.exe` через PyInstaller.
4. Генерирует `installer.iss` для Inno Setup.

### Установщик

Установи [Inno Setup](https://jrsoftware.org/isinfo.php) и скомпилируй `installer.iss`.

Результат: `installer/CritiCat_Setup.exe`

### PyInstaller вручную

`pyinstaller --onefile --windowed --icon=criticat.ico --name=CritiCat --hidden-import=PySide6.QtCore --hidden-import=PySide6.QtGui --hidden-import=PySide6.QtWidgets --hidden-import=requests --hidden-import=cryptography main.py`

---

## 🧪 Тестирование

### Unit-тесты провайдера Swelab

`pytest tests/test_swelab_com_provider.py -v`

Покрывают:

- Парсинг реального XML
- Фильтрацию фона
- Нечисловые ID
- Пустые параметры
- Кэш референсов
- Фильтры очереди
- Склейку разорванных блоков
- `_safe_float` (параметризовано)

### Тест на реальном логе

`pytest tests/test_swelab_from_file.py -v`

Прогоняет сохранённый лог `SwelabAlfa-*.txt` через парсер.

### Интеграционный тест

Требует com0com / socat. Пропускается автоматически, если порт недоступен.

---


## ❓ FAQ

### Swelab не передаёт данные

- Проверь, что PuTTY открыт **до** запуска анализа.
- Убедись, что в `SERIAL SETUP` прибора выбран правильный порт.
- Попробуй `HW-Handshake` вместо `None`.
- Проверь распайку: TX прибора → RX компьютера.

### Данные с Swelab приходят «кракозябрами»

- Не та скорость (попробуй 9600 вместо 19200).
- Не та parity (попробуй `Even` вместо `None`).
- Проверь `bytesize` и `stopbits`.

### VDS-сервер недоступен

- Проверь URL в настройках.
- Проверь API-ключ.
- Убедись, что сервер доступен (`/health` endpoint).
- Логи смотри в вкладке «VDS» → вкладка «Статистика» → консоль.

### База данных не создаётся

`DatabaseManager` пробует создать файл в нескольких местах:

1. По указанному пути.
2. Если нет прав — в `%APPDATA%/CritiCat/`.

Если ошибка — смотри лог в консоли.

### Как добавить нового провайдера ЛИС

1. Создай класс-наследник `BaseProvider`.
2. Реализуй методы `connect`, `disconnect`, `is_connected`, `get_all_test_names`, `get_test_reference_values`, `get_results_for_tests`.
3. Зарегистрируй в `ProviderFactory.create()`.

---

## 🔗 Связанные репозитории

- **Основной репозиторий**: [knyazhninstanislav/criticat](https://github.com/knyazhninstanislav/criticat)

---
