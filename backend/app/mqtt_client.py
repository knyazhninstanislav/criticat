# mqtt_client.py
import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import threading
import time

logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self, host: str, port: int, username: str, password: str, client_id: str = "backend_service"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id
        self.client = None
        self.is_connected = False
        
    def connect(self):
        """Подключение к MQTT брокеру"""
        try:
            self.client = mqtt.Client(
                client_id=self.client_id,
                clean_session=True,
                protocol=mqtt.MQTTv311
            )
            
            # Устанавливаем callback'и
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Аутентификация
            if self.username:
                self.client.username_pw_set(self.username, self.password)
            
            # Подключение
            self.client.connect(self.host, self.port, 60)
            
            # Запускаем цикл в отдельном потоке
            self.client.loop_start()
            
            # Ждем подключения
            timeout = 10
            start = time.time()
            while not self.is_connected and time.time() - start < timeout:
                time.sleep(0.1)
            
            if not self.is_connected:
                logger.error("Failed to connect to MQTT broker")
                return False
            
            logger.info(f"Connected to MQTT broker at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback при подключении"""
        if rc == 0:
            self.is_connected = True
            logger.info("MQTT connected successfully")
            
            # Подписываемся на нужные топики
            self.client.subscribe("criticat/confirmations/+", qos=1)
            self.client.subscribe("criticat/rejections/+", qos=1)
            self.client.subscribe("criticat/mobile/status", qos=1)
            
        else:
            logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback при отключении"""
        self.is_connected = False
        logger.warning(f"MQTT disconnected with code {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback при получении сообщения"""
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            logger.info(f"Received MQTT message on {msg.topic}: {payload}")
            
            # Обработка подтверждений
            if msg.topic.startswith("criticat/confirmations/accept/"):
                self._handle_confirmation(payload, "accepted")
            elif msg.topic.startswith("criticat/confirmations/reject/"):
                self._handle_confirmation(payload, "rejected")
            elif msg.topic.startswith("criticat/mobile/status"):
                self._handle_mobile_status(payload)
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _handle_confirmation(self, payload: Dict, action: str):
        """Обработка подтверждения от мобильного приложения"""
        result_id = payload.get('result_id')
        user = payload.get('user')
        timestamp = payload.get('timestamp')
        
        if not result_id:
            logger.error("Confirmation without result_id")
            return
        
        # Здесь обновляем статус в базе данных
        from .database import SessionLocal, AnonymizedResult
        db = SessionLocal()
        try:
            result = db.query(AnonymizedResult).filter(
                AnonymizedResult.id == result_id
            ).first()
            
            if result:
                result.status = 'confirmed' if action == 'accepted' else 'rejected'
                result.confirmed_by = user
                result.confirmed_at = datetime.utcnow()
                db.commit()
                logger.info(f"Result {result_id} {action} by {user}")
                
                # Отправляем подтверждение в Desktop через MQTT
                self.publish(
                    f"criticat/system/confirmation",
                    {
                        'result_id': result_id,
                        'action': action,
                        'confirmed_by': user,
                        'confirmed_at': timestamp
                    }
                )
            else:
                logger.warning(f"Result {result_id} not found")
                
        except Exception as e:
            logger.error(f"Error updating result: {e}")
            db.rollback()
        finally:
            db.close()
    
    def _handle_mobile_status(self, payload: Dict):
        """Обработка статуса мобильного приложения"""
        status = payload.get('status')
        device_id = payload.get('device_id')
        logger.info(f"Mobile device {device_id} status: {status}")
    
    def publish(self, topic: str, payload: Dict, qos: int = 1):
        """Публикация сообщения"""
        if not self.is_connected:
            logger.error("Cannot publish: not connected")
            return False
        
        try:
            message = json.dumps(payload)
            result = self.client.publish(topic, message, qos=qos)
            
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to publish to {topic}: {result.rc}")
                return False
            
            logger.debug(f"Published to {topic}: {payload}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}")
            return False
    
    def publish_result(self, result_data: Dict):
        """Публикация нового результата для мобильных устройств"""
        topic = f"criticat/results/{result_data.get('result_id', 'unknown')}"
        return self.publish(topic, result_data)
    
    def disconnect(self):
        """Отключение от брокера"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
            logger.info("Disconnected from MQTT broker")

# Глобальный экземпляр
mqtt_client = MQTTClient(
    host='localhost',  # или ваш IP
    port=1883,
    username='backend_service',
    password='your_backend_password'
)
