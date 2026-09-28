# providers/swelab_com_provider.py
"""
Провайдер ЛИС для анализатора Swelab Alfa (BM800) через COM-порт.

Читает XML-поток с RS-232, парсит <sample> блоки и отдаёт их
в виде LisResult — совместимо с MockLisProvider.
"""

import re
import time
import threading
import queue
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional

import serial  # pyserial

from .base import LisProvider, LisResult


# ---------- Константы Swelab ----------

# Параметры порта по умолчанию
DEFAULT_BAUD = 19200
DEFAULT_BYTESIZE = serial.EIGHTBITS
DEFAULT_PARITY = serial.PARITY_NONE
DEFAULT_STOPBITS = serial.STOPBITS_ONE

# Маркеры сообщений
RE_SAMPLE = re.compile(rb"<sample>.*?</sample>", re.DOTALL)


class SwelabComProvider(LisProvider):
    """
    Провайдер, читающий результаты с анализатора Swelab Alfa через COM-порт.

    Открывает порт, слушает в фоновом потоке, разбирает XML,
    складывает LisResult в очередь.
    """

    def __init__(
        self,
        port: str = "COM3",
        baudrate: int = DEFAULT_BAUD,
        timeout: float = 1.0,
        skip_background: bool = True,
    ):
        """
        Args:
            port: имя COM-порта ('COM3', '/dev/ttyUSB0', ...)
            baudrate: скорость (19200 по умолчанию для Swelab)
            timeout: таймаут чтения, сек
            skip_background: пропускать AUTOBACKGROUND (фон)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.skip_background = skip_background

        self.ser: Optional[serial.Serial] = None

        # Очередь готовых результатов
        self._results_queue: queue.Queue[LisResult] = queue.Queue()

        # Буфер для сборки XML-блоков (может прийти по частям)
        self._buffer = b""

        # Поток-читатель
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Счётчики
        self._msg_counter = 0

        # Кэш референсов (собираем из самих результатов)
        self._refs_cache: Dict[str, Dict[str, float]] = {}

    # ---------- Соединение ----------

    def connect(self) -> bool:
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=DEFAULT_BYTESIZE,
                parity=DEFAULT_PARITY,
                stopbits=DEFAULT_STOPBITS,
                timeout=self.timeout,
            )
            print(f"[Swelab] ✅ Порт {self.port} открыт ({self.baudrate} 8N1)")

            self._stop_event.clear()
            self._reader_thread = threading.Thread(
                target=self._reader_loop, daemon=True, name="SwelabReader"
            )
            self._reader_thread.start()
            return True
        except Exception as e:
            print(f"[Swelab] ❌ Ошибка открытия порта {self.port}: {e}")
            self.ser = None
            return False

    def disconnect(self) -> None:
        self._stop_event.set()
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=2.0)
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = None
        print("[Swelab] Порт закрыт")

    def is_connected(self) -> bool:
        return self.ser is not None and self.ser.is_open

    # ---------- Фоновое чтение ----------

    def _reader_loop(self) -> None:
        """Крутится в отдельном потоке, читает байты и ищет <sample> блоки."""
        while not self._stop_event.is_set():
            try:
                chunk = self.ser.read(4096)
                if not chunk:
                    continue

                self._buffer += chunk
                self._extract_samples()

                # Защита от переполнения буфера
                if len(self._buffer) > 5_000_000:
                    print("[Swelab] ⚠ Буфер переполнен, сброс")
                    self._buffer = b""

            except serial.SerialException as e:
                print(f"[Swelab] ❌ Ошибка чтения: {e}")
                break
            except Exception as e:
                print(f"[Swelab] ❌ Неожиданная ошибка: {e}")
                time.sleep(0.5)

    def _extract_samples(self) -> None:
        """Ищет завершённые <sample>...</sample> в буфере и парсит их."""
        while True:
            m = RE_SAMPLE.search(self._buffer)
            if not m:
                # Не нашли закрытого блока — ждём ещё данных.
                # Но если буфер уже большой и <sample> открыт, а </sample> нет —
                # возможно, что-то пошло не так. Оставим как есть.
                return

            block = m.group(0)
            # Всё до конца блока — выбрасываем из буфера
            self._buffer = self._buffer[m.end():]

            try:
                self._handle_sample(block)
            except Exception as e:
                print(f"[Swelab] ❌ Ошибка парсинга sample: {e}")

    def _handle_sample(self, raw: bytes) -> None:
        """Парсит один <sample> и складывает LisResult в очередь."""
        # Декодируем; Swelab шлёт ASCII/UTF-8
        xml_str = raw.decode("utf-8", errors="replace")

        root = ET.fromstring(xml_str)

        # --- smpinfo ---
        info: Dict[str, str] = {}
        for p in root.findall("./smpinfo/p"):
            name = (p.findtext("n") or "").strip()
            val = p.findtext("v")
            info[name] = (val or "").strip()

        sample_id_raw = info.get("ID", "").strip()
        seq = info.get("SEQ", "").strip()
        date = info.get("DATE", "").strip()
        apna = info.get("APNA", "").strip()

        # Фон пропускаем
        if self.skip_background and sample_id_raw.upper() == "AUTOBACKGROUND":
            print(f"[Swelab] ⏭ Пропущен фон (SEQ={seq})")
            return

        # ids — пробуем вытащить число из ID
        try:
            ids = int(sample_id_raw)
        except (ValueError, TypeError):
            ids = 0  # например, штрих-код с буквами

        # id — используем SEQ, если он есть; иначе счётчик
        try:
            row_id = int(seq) if seq else self._msg_counter
        except ValueError:
            self._msg_counter += 1
            row_id = self._msg_counter

        # --- smpresults ---
        added = 0
        for p in root.findall("./smpresults/p"):
            name = (p.findtext("n") or "").strip()
            val_txt = p.findtext("v")
            if val_txt is None or val_txt.strip() == "":
                continue  # параметр не измерялся

            try:
                value = float(val_txt.strip().replace(",", "."))
            except ValueError:
                continue

            ref_low_txt = p.findtext("l")
            ref_high_txt = p.findtext("h")
            ref_low = self._safe_float(ref_low_txt)
            ref_high = self._safe_float(ref_high_txt)

            # Кэшируем референсы
            if ref_low is not None and ref_high is not None:
                self._refs_cache[name] = {
                    "ref_lower": ref_low,
                    "ref_upper": ref_high,
                }

            result = LisResult(
                id=row_id,
                ids=ids,
                full_name=sample_id_raw or "—",
                department="",  # заполнит ЛИС по ids
                test_name=name,
                result_value=value,
                ref_lower=ref_low,
                ref_upper=ref_high,
            )
            self._results_queue.put(result)
            added += 1

        print(
            f"[Swelab] 📥 SEQ={seq} ID={sample_id_raw} "
            f"({date}, {apna}) — {added} параметров"
        )

    @staticmethod
    def _safe_float(txt: Optional[str]) -> Optional[float]:
        if txt is None:
            return None
        txt = txt.strip().replace(",", ".")
        if not txt:
            return None
        try:
            return float(txt)
        except ValueError:
            return None

    # ---------- Интерфейс LisProvider ----------

    def get_all_test_names(self) -> List[str]:
        """Уникальные имена тестов из кэша референсов."""
        return sorted(self._refs_cache.keys())

    def get_test_reference_values(self) -> Dict[str, Dict[str, float]]:
        """Референсные значения, накопленные из результатов."""
        return dict(self._refs_cache)

    def get_results_for_tests(
        self,
        test_names: List[str],
        excluded_ids: List[int],
    ) -> List[LisResult]:
        """
        Забирает из очереди всё, что накопилось, фильтрует по:
        - test_names (если список непустой)
        - excluded_ids (исключает уже обработанные id)
        """
        drained: List[LisResult] = []
        while True:
            try:
                drained.append(self._results_queue.get_nowait())
            except queue.Empty:
                break

        if not drained:
            return []

        test_set = set(test_names) if test_names else None
        excluded_set = set(excluded_ids) if excluded_ids else set()

        filtered = [
            r
            for r in drained
            if (test_set is None or r.test_name in test_set)
            and r.id not in excluded_set
        ]
        return filtered

    # ---------- Дополнительно ----------

    def get_results_nowait(self) -> List[LisResult]:
        """
        Удобный метод: отдать всё из очереди без фильтрации.
        Для GUI, где не нужен протокол 'excluded_ids'.
        """
        out = []
        while True:
            try:
                out.append(self._results_queue.get_nowait())
            except queue.Empty:
                break
        return out

    def __repr__(self) -> str:
        return (
            f"<SwelabComProvider port={self.port} "
            f"baud={self.baudrate} connected={self.is_connected()}>"
        )