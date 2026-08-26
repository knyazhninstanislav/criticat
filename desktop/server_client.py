import requests
import json
import logging
import threading
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class ServerClient:
    """Клиент для взаимодействия с VDS сервером"""

    def __init__(self, server_url: str = "", api_key: str = ""):
        self.server_url = server_url.rstrip('/') if server_url else ""
        self.api_key = api_key
        self.session = None
        self._polling_thread = None
        self._polling_active = False
        self._callbacks: List[Callable] = []
        self._processed_keys = set()
        self._sent_results = set()
        self._lock = threading.Lock()
        self._auth_verified = False
        self._last_auth_check = None

        self._init_session(api_key)

    def _init_session(self, api_key: str = ""):
        """Инициализация сессии с заголовками авторизации"""
        try:
            if self.session:
                self.session.close()

            self.session = requests.Session()

            # Базовые заголовки
            self.session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'CritiCat-Desktop/1.0',
            })

            # Заголовки авторизации
            if api_key:
                self.session.headers.update({
                    'X-API-Key': api_key,
                    'Authorization': f'Bearer {api_key}',
                })

            logger.info("Сессия инициализирована")
        except Exception as e:
            logger.error(f"Ошибка инициализации сессии: {e}")
            self.session = requests.Session()

    def set_server_url(self, url: str):
        """Установка URL сервера"""
        with self._lock:
            self.server_url = url.rstrip('/') if url else ""
            self._auth_verified = False  # Сбрасываем проверку при смене URL

    def set_api_key(self, key: str):
        """Установка API ключа"""
        with self._lock:
            self.api_key = key
            self._auth_verified = False  # Сбрасываем проверку при смене ключа
            try:
                if self.session:
                    self.session.headers.update({
                        'X-API-Key': key,
                        'Authorization': f'Bearer {key}',
                    })
                else:
                    self._init_session(key)
            except:
                self._init_session(key)

    def is_configured(self) -> bool:
        """Проверка настройки"""
        return bool(self.server_url and self.api_key)

    def verify_auth(self) -> tuple:
        """Проверка авторизации по API ключу"""
        if not self.server_url:
            return False, "URL сервера не указан"

        if not self.api_key:
            return False, "API ключ не указан"

        try:
            # Отправляем запрос на проверку авторизации
            response = self.session.get(
                f"{self.server_url}/api/v1/auth/verify",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self._auth_verified = True
                self._last_auth_check = datetime.now()
                return True, data.get('message', 'Авторизация успешна')
            elif response.status_code == 401:
                self._auth_verified = False
                return False, "Неверный API ключ"
            elif response.status_code == 403:
                self._auth_verified = False
                return False, "Доступ запрещен"
            else:
                self._auth_verified = False
                return False, f"HTTP ошибка: {response.status_code}"

        except requests.exceptions.ConnectionError:
            return False, "Не удалось подключиться к серверу"
        except requests.exceptions.Timeout:
            return False, "Таймаут соединения"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"

    def test_connection(self) -> tuple:
        """Проверка соединения (включая авторизацию)"""
        if not self.server_url:
            return False, "URL сервера не указан"

        try:
            # Сначала проверяем доступность сервера
            response = self.session.get(f"{self.server_url}/health", timeout=10)

            if response.status_code == 200:
                # Сервер доступен, проверяем авторизацию
                auth_success, auth_message = self.verify_auth()
                if auth_success:
                    return True, f"Сервер доступен, {auth_message}"
                else:
                    return False, f"Сервер доступен, но {auth_message}"
            elif response.status_code == 401:
                return False, "Неверный API ключ"
            else:
                return False, f"HTTP ошибка: {response.status_code}"

        except Exception as e:
            return False, f"Ошибка: {str(e)}"

    def _check_auth_before_request(self) -> bool:
        """Проверка авторизации перед запросом"""
        # Если уже проверяли недавно (менее 5 минут назад)
        if self._auth_verified and self._last_auth_check:
            if (datetime.now() - self._last_auth_check).seconds < 300:
                return True

        # Проверяем авторизацию
        success, _ = self.verify_auth()
        return success

    def send_single_result(self, ids: int, department: str, test_name: str,
                           result_value: float, ref_lower: Optional[float] = None,
                           ref_upper: Optional[float] = None,
                           deviation_percent: Optional[float] = None,
                           monitor_type: str = 'both') -> Dict:
        """Отправка одного результата (с проверкой авторизации)"""
        if not self.server_url:
            return {'success': False, 'message': 'URL сервера не указан'}

        if not self.api_key:
            return {'success': False, 'message': 'API ключ не указан'}

        # Проверяем авторизацию
        if not self._check_auth_before_request():
            return {'success': False, 'message': 'Ошибка авторизации'}

        result_key = f"{ids}|{test_name}|{result_value}"

        with self._lock:
            if result_key in self._sent_results:
                return {'success': True, 'skipped': True}

        try:
            payload = {
                'ids': int(ids),
                'department': str(department),
                'test_name': str(test_name),
                'result_value': float(result_value),
                'ref_lower': float(ref_lower) if ref_lower is not None else 0,
                'ref_upper': float(ref_upper) if ref_upper is not None else 0,
                'deviation_percent': float(deviation_percent) if deviation_percent is not None else 0,
                'monitor_type': str(monitor_type),
            }

            response = self.session.post(
                f"{self.server_url}/api/v1/results",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                with self._lock:
                    self._sent_results.add(result_key)
                return response.json()
            elif response.status_code == 401:
                self._auth_verified = False
                return {'success': False, 'message': 'Неверный API ключ'}
            elif response.status_code == 403:
                return {'success': False, 'message': 'Доступ запрещен'}
            else:
                return {'success': False, 'message': f"HTTP {response.status_code}"}

        except Exception as e:
            return {'success': False, 'message': str(e)}

    def send_results(self, results: List[Dict[str, Any]]) -> Dict:
        """Отправка нескольких результатов"""
        if not self.is_configured():
            return {'success': False, 'message': 'Сервер не настроен'}

        sent_count = 0
        skipped_count = 0
        failed_count = 0

        for r in results:
            try:
                response = self.send_single_result(
                    ids=r.get('ids', 0),
                    department=r.get('department', ''),
                    test_name=r.get('test_name', ''),
                    result_value=r.get('result_value', 0),
                    ref_lower=r.get('ref_lower'),
                    ref_upper=r.get('ref_upper'),
                    deviation_percent=r.get('deviation_percent'),
                    monitor_type=r.get('monitor_type', 'both'),
                )

                if response.get('success'):
                    if response.get('skipped'):
                        skipped_count += 1
                    else:
                        sent_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1

            time.sleep(0.3)

        return {
            'success': sent_count > 0,
            'sent_count': sent_count,
            'skipped_count': skipped_count,
            'failed_count': failed_count,
        }

    def get_pending_confirmations(self) -> List[Dict]:
        """Получение подтверждений (с проверкой авторизации)"""
        if not self.is_configured():
            return []

        try:
            response = self.session.get(
                f"{self.server_url}/api/v1/results/confirmed",
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return data.get('results', [])
            elif response.status_code == 401:
                self._auth_verified = False
                logger.error("Неверный API ключ")

            return []
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return []

    def acknowledge_confirmations(self, result_keys: List[str]) -> Dict:
        """Подтверждение получения"""
        if not self.is_configured():
            return {'success': False}

        try:
            response = self.session.post(
                f"{self.server_url}/api/v1/results/acknowledge",
                json={'result_keys': result_keys},
                timeout=30
            )

            if response.status_code == 200:
                self._processed_keys.update(result_keys)
                return response.json()
            elif response.status_code == 401:
                return {'success': False, 'message': 'Неверный API ключ'}
            return {'success': False}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def register_callback(self, callback: Callable):
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def start_polling(self, interval: int = 30):
        with self._lock:
            if self._polling_thread and self._polling_thread.is_alive():
                return
            self._polling_active = True
            self._polling_thread = threading.Thread(
                target=self._polling_loop, args=(interval,), daemon=True
            )
            self._polling_thread.start()
            logger.info(f"Опрос запущен ({interval}с)")

    def stop_polling(self):
        with self._lock:
            self._polling_active = False
        if self._polling_thread:
            self._polling_thread.join(timeout=5)
            self._polling_thread = None

    def _polling_loop(self, interval: int):
        while self._polling_active:
            try:
                confirmations = self.get_pending_confirmations()
                if confirmations:
                    for callback in self._callbacks:
                        try:
                            callback(confirmations)
                        except:
                            pass
                    keys = [c.get('result_key') for c in confirmations if isinstance(c, dict)]
                    if keys:
                        self.acknowledge_confirmations(keys)
            except:
                pass

            for _ in range(interval):
                if not self._polling_active:
                    break
                time.sleep(1)

    def close(self):
        self.stop_polling()
        try:
            if self.session:
                self.session.close()
                self.session = None
        except:
            pass


# Синглтон
server_client = ServerClient()