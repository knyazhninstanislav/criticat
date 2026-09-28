# tests/test_swelab_com_provider.py
"""
Тесты для providers.swelab_com_provider.

Запуск:
    pytest tests/test_swelab_com_provider.py -v
    # или
    python -m pytest tests/test_swelab_com_provider.py -v
"""

import time
import queue
import pytest

from desktop.providers.swelab_com_provider import SwelabComProvider
from desktop.providers.base import BaseResult


# ---------- Эталонный XML (вырезан из реального лога) ----------

SAMPLE_BLOOD = b"""<sample>
<ver>1.1</ver>
<instrinfo>
<p><n>PRDI</n><v>BM800</v></p>
<p><n>FIWV</n><v>2.9.6</v></p>
<p><n>SNO</n><v>28161</v></p>
</instrinfo>
<smpinfo>
<p><n>ID</n><v>32072272</v></p>
<p><n>SEQ</n><v>6837</v></p>
<p><n>DATE</n><v>2026-09-14T17:42:50</v></p>
<p><n>APNU</n><v>1</v></p>
<p><n>APNA</n><v>BLOOD</v></p>
</smpinfo>
<smpresults>
<p><n>RBC</n><v>4.55</v><f>ER</f><l>3.90</l><h>5.00</h></p>
<p><n>MCV</n><v>83.4</v><l>70.0</l><h>90.0</h></p>
<p><n>HGB</n><v>15.4</v><f>ER</f><l>12.0</l><h>16.0</h></p>
<p><n>WBC</n><v>11.7</v><f>ER</f><l>4.0</l><h>9.0</h></p>
<p><n>LA</n><v>4.4</v><f>ER</f><l>0.5</l><h>5.0</h></p>
<p><n>GR</n><v>52.6</v><f>ER</f><l>55.0</l><h>70.0</h></p>
<p><n>MPV</n><l>6.0</l><h>10.0</h></p>
</smpresults>
<tparams>
<p><n>RCT</n><v>14744</v></p>
<p><n>WCT</n><v>12940</v></p>
</tparams>
</sample>"""

SAMPLE_BACKGROUND = b"""<sample>
<ver>1.1</ver>
<instrinfo>
<p><n>PRDI</n><v>BM800</v></p>
</instrinfo>
<smpinfo>
<p><n>ID</n><v>AUTOBACKGROUND</v></p>
<p><n>SEQ</n><v>6835</v></p>
<p><n>DATE</n><v>2026-09-14T06:52:12</v></p>
<p><n>APNU</n><v>2</v></p>
<p><n>APNA</n><v>BACKGROUND</v></p>
</smpinfo>
<smpresults>
<p><n>RBC</n><v>0.00</v><f>ER</f><l>0.00</l><h>0.01</h></p>
<p><n>HGB</n><v>0.1</v><f>ER</f><l>0.0</l><h>0.2</h></p>
<p><n>WBC</n><v>0.0</v><f>ER</f><l>0.0</l><h>0.1</h></p>
</smpresults>
<tparams>
<p><n>RCT</n><v>14774</v></p>
</tparams>
</sample>"""


# ---------- Фикстуры ----------

@pytest.fixture
def provider():
    """
    Провайдер без реального порта.
    Мы не вызываем connect() — тестируем только логику парсинга и очередь.
    """
    p = SwelabComProvider(port="FAKE", baudrate=19200, skip_background=True)
    yield p
    # Ничего закрывать не надо — порт не открывался


@pytest.fixture
def provider_with_bg():
    """Провайдер, который НЕ пропускает фон."""
    return SwelabComProvider(port="FAKE", skip_background=False)


# ---------- Парсинг ----------

def test_parse_sample_real(provider):
    """Один реальный <sample> → 6 BaseResult (MPV без значения — пропущен)."""
    provider._handle_sample(SAMPLE_BLOOD)

    results = provider.get_results_nowait()
    assert len(results) == 6

    by_name = {r.test_name: r for r in results}

    # Проверяем ключевые поля
    assert by_name["RBC"].result_value == 4.55
    assert by_name["RBC"].ref_lower == 3.90
    assert by_name["RBC"].ref_upper == 5.00

    assert by_name["HGB"].result_value == 15.4
    assert by_name["WBC"].result_value == 11.7

    # Все результаты одного образца
    for r in results:
        assert r.id == 6837
        assert r.ids == 32072272
        assert r.full_name == "32072272"

    # MPV без <v> не должен попасть
    assert "MPV" not in by_name


def test_skip_background(provider):
    """Фон отбрасывается при skip_background=True."""
    provider._handle_sample(SAMPLE_BACKGROUND)
    assert provider.get_results_nowait() == []


def test_keep_background(provider_with_bg):
    """Фон НЕ отбрасывается при skip_background=False."""
    provider_with_bg._handle_sample(SAMPLE_BACKGROUND)
    results = provider_with_bg.get_results_nowait()
    assert len(results) == 3
    assert {r.test_name for r in results} == {"RBC", "HGB", "WBC"}


def test_id_not_numeric(provider):
    """Штрих-код с буквами → ids=0, full_name сохранён."""
    xml = SAMPLE_BLOOD.replace(b"<v>32072272</v>", b"<v>ABC-123-XYZ</v>")
    provider._handle_sample(xml)

    results = provider.get_results_nowait()
    assert len(results) > 0
    assert all(r.ids == 0 for r in results)
    assert all(r.full_name == "ABC-123-XYZ" for r in results)


def test_empty_param_skipped(provider):
    """<p> без <v> не превращается в BaseResult."""
    xml = b"""<sample>
    <smpinfo>
    <p><n>ID</n><v>100</v></p>
    <p><n>SEQ</n><v>1</v></p>
    </smpinfo>
    <smpresults>
    <p><n>WBC</n><v>5.5</v><l>4.0</l><h>9.0</h></p>
    <p><n>RBC</n></p>
    <p><n>HGB</n><v></v></p>
    </smpresults>
    </sample>"""
    provider._handle_sample(xml)
    results = provider.get_results_nowait()
    assert len(results) == 1
    assert results[0].test_name == "WBC"


# ---------- Референсы ----------

def test_refs_cached(provider):
    """Референсы из <l>, <h> попадают в кэш."""
    provider._handle_sample(SAMPLE_BLOOD)
    refs = provider.get_test_reference_values()

    assert "RBC" in refs
    assert refs["RBC"]["ref_lower"] == 3.90
    assert refs["RBC"]["ref_upper"] == 5.00
    assert refs["WBC"]["ref_lower"] == 4.0
    assert refs["WBC"]["ref_upper"] == 9.0


def test_get_all_test_names(provider):
    """get_all_test_names отдаёт отсортированный список из кэша."""
    provider._handle_sample(SAMPLE_BLOOD)
    names = provider.get_all_test_names()
    assert names == sorted(names)
    assert "WBC" in names
    assert "HGB" in names
    assert "MPV" not in names  # без значения — не кэшируется


# ---------- Очередь и фильтры ----------

def test_queue_drain(provider):
    """get_results_nowait опустошает очередь."""
    provider._handle_sample(SAMPLE_BLOOD)
    first = provider.get_results_nowait()
    second = provider.get_results_nowait()

    assert len(first) == 6
    assert second == []


def test_test_names_filter(provider):
    """get_results_for_tests фильтрует по именам тестов."""
    provider._handle_sample(SAMPLE_BLOOD)
    results = provider.get_results_for_tests(
        test_names=["WBC", "HGB"],
        excluded_ids=[],
    )
    assert {r.test_name for r in results} == {"WBC", "HGB"}
    assert len(results) == 2


def test_excluded_ids(provider):
    """excluded_ids исключает уже обработанные строки."""
    provider._handle_sample(SAMPLE_BLOOD)
    results = provider.get_results_for_tests(
        test_names=[],
        excluded_ids=[6837],
    )
    assert results == []


def test_empty_test_names_means_all(provider):
    """Пустой test_names → отдаём всё."""
    provider._handle_sample(SAMPLE_BLOOD)
    results = provider.get_results_for_tests(test_names=[], excluded_ids=[])
    assert len(results) == 6


def test_is_connected_false_without_port(provider):
    """Без connect() порт не открыт."""
    assert provider.is_connected() is False


# ---------- Разбор буфера (склейка частей) ----------

def test_extract_samples_partial(provider):
    """Блок, разорванный на куски, собирается корректно."""
    # Кладём в буфер первую половину
    half = len(SAMPLE_BLOOD) // 2
    provider._buffer = SAMPLE_BLOOD[:half]
    provider._extract_samples()
    assert provider._buffer == SAMPLE_BLOOD[:half]  # ничего не извлекли

    # Дописываем вторую половину
    provider._buffer += SAMPLE_BLOOD[half:]
    provider._extract_samples()

    assert provider._buffer == b""  # весь блок ушёл
    results = provider.get_results_nowait()
    assert len(results) == 6


def test_extract_samples_two_blocks(provider):
    """Два блока подряд → оба разобраны."""
    provider._buffer = SAMPLE_BLOOD + SAMPLE_BLOOD
    provider._extract_samples()
    results = provider.get_results_nowait()
    assert len(results) == 12


def test_extract_garbage_between_blocks(provider):
    """Мусор между блоками не ломает парсер."""
    provider._buffer = b"garbage\n" + SAMPLE_BLOOD + b"\n\r\n\r\n" + SAMPLE_BLOOD
    provider._extract_samples()
    results = provider.get_results_nowait()
    assert len(results) == 12


# ---------- _safe_float ----------

@pytest.mark.parametrize("inp,expected", [
    ("1.5", 1.5),
    ("1,5", 1.5),
    (" 2.0 ", 2.0),
    ("-3.14", -3.14),
    ("", None),
    (None, None),
    ("abc", None),
])
def test_safe_float(inp, expected):
    assert SwelabComProvider._safe_float(inp) == expected


# ---------- Интеграционный тест с виртуальным COM ----------

@pytest.mark.skipif(
    not pytest.importorskip("serial", reason="pyserial не установлен"),
    reason="нужен pyserial и, желательно, com0com / socat",
)
def test_integration_loopback():
    """
    Полный цикл: пишем в один конец виртуальной пары, читаем с другого.

    Требует:
      - Windows: com0com (пара COM10 <-> COM11)
      - Linux:   socat PTY,link=/tmp/ttyV0 PTY,link=/tmp/ttyV1
    Меняй порты ниже под свою пару.
    """
    import serial

    WRITE_PORT = "COM11"   # <-- поменяй
    READ_PORT = "COM10"    # <-- поменяй

    try:
        writer = serial.Serial(WRITE_PORT, 19200, timeout=1)
    except serial.SerialException:
        pytest.skip(f"Виртуальный порт {WRITE_PORT} недоступен")

    provider = SwelabComProvider(port=READ_PORT, baudrate=19200, skip_background=True)
    assert provider.connect() is True

    try:
        # Даём потоку-читателю время встать на чтение
        time.sleep(0.2)

        # Шлём XML
        writer.write(SAMPLE_BLOOD)
        writer.flush()

        # Ждём, пока провайдер разберёт (до 2 сек)
        deadline = time.time() + 2.0
        results = []
        while time.time() < deadline:
            results = provider.get_results_nowait()
            if results:
                break
            time.sleep(0.05)

        assert len(results) == 6
        assert {r.test_name for r in results} >= {"RBC", "HGB", "WBC"}

    finally:
        provider.disconnect()
        writer.close()