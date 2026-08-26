import json
import logging
import threading
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTClient:
    """Клиент для взаимодействия с MQTT брокером"""

    # Стандартные топики
    TOPIC_RESULTS = "criticat/results"
    TOPIC_CONFIRMATIONS = "criticat/confirmations"
    TOPIC_ACKNOWLEDGE = "criticat/acknowledge"
    TOPIC_STATUS = "criticat/status"
    TOPIC_USERS = "criticat/users"

    def __init__(self, broker_host: str = "", broker_port: int = 1883,
                 client_id: str = "", username: str = "", password: str = "",
                 use_tls: bool = False):
        """
        Инициализация MQTT клиента

        Args:
            broker_host: Адрес MQTT брокера
            broker_port: Порт MQTT брокера (по умолчанию 1883)
            client_id: ID клиента (если пусто - генерируется автоматически)
            username: Имя пользователя для аутентификации
            password: Пароль для аутентификации
            use_tls: Использовать TLS/SSL
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"criticat-desktop-{int(time.time())}"
        self.username = username
        self.password = password
        self.use_tls = use_tls

        self.client = None
        self._connected = False
        self._polling_thread = None
        self._polling_active = False
        self._callbacks: List[Callable] = []
        self._processed_keys = set()
        self._sent_results = set()
        self._lock = threading.Lock()
        self._last_connection_attempt = None

        self._init_client()

    def _init_client(self):
        """Инициализация MQTT клиента"""
        try:
            if self.client:
                try:
                    self.client.disconnect()
                except:
                    pass
                self.client = None

            # Создаем клиент с протоколом v5
            self.client = mqtt.Client(
                client_id=self.client_id,
                protocol=mqtt.MQTTv5,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )

            # Настройка аутентификации
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)

            # Настройка TLS
            if self.use_tls:
                self.client.tls_set(cert_reqs=mqtt.ssl.CERT_NONE)
                self.client.tls_insecure_set(True)

            # Настройка колбэков
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_publish = self._on_publish

            logger.info(f"MQTT клиент инициализирован (ID: {self.client_id})")

        except Exception as e:
            logger.error(f"Ошибка инициализации MQTT: {e}")
            self.client = None

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """Обработчик подключения"""
        if reason_code == 0:
            self._connected = True
            logger.info(f"MQTT подключен к {self.broker_host}:{self.broker_port}")

            # Подписываемся на топики
            self._subscribe_topics()

            # Публикуем статус
            self.publish_status("online", "Клиент подключен")
        else:
            self._connected = False
            logger.error(f"Ошибка подключения MQTT: {reason_code}")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        """Обработчик отключения"""
        self._connected = False
        logger.warning(f"MQTT отключен: {reason_code}")

    def _on_message(self, client, userdata, message):
        """Обработчик входящих сообщений"""
        try:
            topic = message.topic
            payload = json.loads(message.payload.decode('utf-8'))

            logger.debug(f"Получено MQTT сообщение: {topic}")

            # Обработка подтверждений
            if topic == self.TOPIC_CONFIRMATIONS:
                self._handle_confirmations(payload)
            elif topic == self.TOPIC_ACKNOWLEDGE:
                self._handle_acknowledge(payload)
            elif topic == self.TOPIC_STATUS:
                self._handle_status(payload)

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")

    def _on_publish(self, client, userdata, mid, reason_code, properties):
        """Обработчик публикации"""
        if reason_code != 0:
            logger.warning(f"Ошибка публикации: {reason_code}")

    def _subscribe_topics(self):
        """Подписка на топики"""
        if not self.client or not self._connected:
            return

        topics = [
            (self.TOPIC_CONFIRMATIONS, 2),  # QoS 2 - гарантированная доставка
            (self.TOPIC_ACKNOWLEDGE, 2),
            (self.TOPIC_STATUS, 1),
        ]

        for topic, qos in topics:
            try:
                self.client.subscribe(topic, qos=qos)
                logger.debug(f"Подписка на {topic} (QoS {qos})")
            except Exception as e:
                logger.error(f"Ошибка подписки на {topic}: {e}")

    def _handle_confirmations(self, payload: Dict):
        """Обработка подтверждений"""
        confirmations = payload.get('results', [])
        if not confirmations:
            return

        # Уведомляем колбэки
        for callback in self._callbacks:
            try:
                callback(confirmations)
            except Exception as e:
                logger.error(f"Ошибка в колбэке: {e}")

        # Подтверждаем получение
        keys = [c.get('result_key') for c in confirmations if isinstance(c, dict)]
        if keys:
            self.acknowledge_confirmations(keys)

    def _handle_acknowledge(self, payload: Dict):
        """Обработка подтверждения получения"""
        result_keys = payload.get('result_keys', [])
        with self._lock:
            self._processed_keys.update(result_keys)
        logger.debug(f"Подтверждены ключи: {len(result_keys)}")

    def _handle_status(self, payload: Dict):
        """Обработка статусных сообщений"""
        status = payload.get('status', 'unknown')
        message = payload.get('message', '')
        logger.info(f"Статус сервера: {status} - {message}")

    # ========== ПУБЛИЧНЫЕ МЕТОДЫ ==========

    def connect(self) -> bool:
        """Подключение к MQTT брокеру"""
        if not self.broker_host:
            logger.error("Адрес брокера не указан")
            return False

        if self._connected:
            return True

        try:
            if not self.client:
                self._init_client()

            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()

            # Ждем подключения
            for _ in range(10):
                if self._connected:
                    return True
                time.sleep(0.5)

            return self._connected

        except Exception as e:
            logger.error(f"Ошибка подключения к MQTT: {e}")
            return False

    def disconnect(self):
        """Отключение от MQTT брокера"""
        self.stop_polling()

        if self.client:
            try:
                self.publish_status("offline", "Клиент отключается")
                self.client.loop_stop()
                self.client.disconnect()
            except Exception as e:
                logger.error(f"Ошибка отключения: {e}")

        self._connected = False
        self.client = None

    def is_connected(self) -> bool:
        """Проверка подключения"""
        return self._connected and self.client is not None

    def is_configured(self) -> bool:
        """Проверка настройки"""
        return bool(self.broker_host and self.broker_port > 0)

    def publish_result(self, ids: int, department: str, test_name: str,
                       result_value: float, ref_lower: Optional[float] = None,
                       ref_upper: Optional[float] = None,
                       deviation_percent: Optional[float] = None,
                       monitor_type: str = 'both') -> bool:
        """
        Публикация одного результата

        Returns:
            bool: Успешность публикации
        """
        if not self.is_connected():
            logger.error("MQTT не подключен")
            return False

        result_key = f"{ids}|{test_name}|{result_value}"

        with self._lock:
            if result_key in self._sent_results:
                return True

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
                'timestamp': datetime.now().isoformat(),
                'client_id': self.client_id,
            }

            # Публикуем с QoS 2
            result = self.client.publish(
                self.TOPIC_RESULTS,
                json.dumps(payload),
                qos=2,
                retain=False
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                with self._lock:
                    self._sent_results.add(result_key)
                logger.debug(f"Опубликован результат: {ids} - {test_name}")
                return True
            else:
                logger.error(f"Ошибка публикации: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Ошибка публикации результата: {e}")
            return False

    def publish_results(self, results: List[Dict[str, Any]]) -> Dict:
        """
        Публикация нескольких результатов

        Returns:
            Dict: Статистика отправки
        """
        if not self.is_connected():
            return {
                'success': False,
                'message': 'MQTT не подключен',
                'sent_count': 0,
                'skipped_count': 0,
                'failed_count': 0
            }

        sent_count = 0
        skipped_count = 0
        failed_count = 0

        for r in results:
            try:
                success = self.publish_result(
                    ids=r.get('ids', 0),
                    department=r.get('department', ''),
                    test_name=r.get('test_name', ''),
                    result_value=r.get('result_value', 0),
                    ref_lower=r.get('ref_lower'),
                    ref_upper=r.get('ref_upper'),
                    deviation_percent=r.get('deviation_percent'),
                    monitor_type=r.get('monitor_type', 'both'),
                )

                if success:
                    sent_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1

            time.sleep(0.1)  # Небольшая задержка между публикациями

        return {
            'success': sent_count > 0,
            'sent_count': sent_count,
            'skipped_count': skipped_count,
            'failed_count': failed_count,
        }

    def acknowledge_confirmations(self, result_keys: List[str]) -> bool:
        """
        Подтверждение получения подтверждений

        Returns:
            bool: Успешность
        """
        if not self.is_connected():
            return False

        try:
            payload = {
                'result_keys': result_keys,
                'client_id': self.client_id,
                'timestamp': datetime.now().isoformat()
            }

            result = self.client.publish(
                self.TOPIC_ACKNOWLEDGE,
                json.dumps(payload),
                qos=2,
                retain=False
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                with self._lock:
                    self._processed_keys.update(result_keys)
                logger.debug(f"Подтверждены ключи: {len(result_keys)}")
                return True

            return False

        except Exception as e:
            logger.error(f"Ошибка подтверждения: {e}")
            return False

    def publish_status(self, status: str, message: str = "") -> bool:
        """
        Публикация статуса клиента

        Returns:
            bool: Успешность
        """
        if not self.is_connected():
            return False

        try:
            payload = {
                'status': status,
                'message': message,
                'client_id': self.client_id,
                'timestamp': datetime.now().isoformat()
            }

            result = self.client.publish(
                self.TOPIC_STATUS,
                json.dumps(payload),
                qos=1,
                retain=True  # Сохраняем последний статус
            )

            return result.rc == mqtt.MQTT_ERR_SUCCESS

        except Exception as e:
            logger.error(f"Ошибка публикации статуса: {e}")
            return False

    def add_user(self, chat_id: str) -> Dict:
        """
        Добавление пользователя (через MQTT)

        Returns:
            Dict: Результат операции
        """
        if not self.is_connected():
            return {'success': False, 'message': 'MQTT не подключен'}

        try:
            payload = {
                'action': 'add_user',
                'chat_id': chat_id,
                'client_id': self.client_id,
                'timestamp': datetime.now().isoformat()
            }

            result = self.client.publish(
                self.TOPIC_USERS,
                json.dumps(payload),
                qos=2,
                retain=False
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Запрос на добавление пользователя {chat_id} отправлен")
                return {'success': True, 'message': 'Запрос отправлен'}

            return {'success': False, 'message': f'Ошибка публикации: {result.rc}'}

        except Exception as e:
            return {'success': False, 'message': str(e)}

    def delete_user(self, chat_id: str) -> Dict:
        """
        Удаление пользователя (через MQTT)

        Returns:
            Dict: Результат операции
        """
        if not self.is_connected():
            return {'success': False, 'message': 'MQTT не подключен'}

        try:
            payload = {
                'action': 'delete_user',
                'chat_id': chat_id,
                'client_id': self.client_id,
                'timestamp': datetime.now().isoformat()
            }

            result = self.client.publish(
                self.TOPIC_USERS,
                json.dumps(payload),
                qos=2,
                retain=False
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Запрос на удаление пользователя {chat_id} отправлен")
                return {'success': True, 'message': 'Запрос отправлен'}

            return {'success': False, 'message': f'Ошибка публикации: {result.rc}'}

        except Exception as e:
            return {'success': False, 'message': str(e)}

    def register_callback(self, callback: Callable):
        """Регистрация колбэка для получения подтверждений"""
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)
                logger.debug("Колбэк зарегистрирован")

    def start_polling(self, interval: int = 30):
        """Запуск фонового опроса (подписки)"""
        with self._lock:
            if self._polling_thread and self._polling_thread.is_alive():
                return

            self._polling_active = True
            self._polling_thread = threading.Thread(
                target=self._polling_loop,
                args=(interval,),
                daemon=True
            )
            self._polling_thread.start()
            logger.info(f"MQTT опрос запущен (интервал {interval}с)")

    def stop_polling(self):
        """Остановка фонового опроса"""
        with self._lock:
            self._polling_active = False

        if self._polling_thread:
            self._polling_thread.join(timeout=5)
            self._polling_thread = None

    def _polling_loop(self, interval: int):
        """Цикл фонового опроса"""
        while self._polling_active:
            try:
                if not self.is_connected():
                    # Пытаемся переподключиться
                    if self.broker_host:
                        logger.warning("MQTT отключен, пытаемся переподключиться...")
                        self.connect()

                # Проверяем наличие неподтвержденных сообщений
                # (основная обработка идет через колбэки _on_message)

            except Exception as e:
                logger.error(f"Ошибка в цикле опроса: {e}")

            for _ in range(interval):
                if not self._polling_active:
                    break
                time.sleep(1)

    def close(self):
        """Закрытие клиента"""
        self.stop_polling()
        self.disconnect()


# Синглтон
mqtt_client = MQTTClient()