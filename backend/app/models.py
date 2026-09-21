# models.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ResultStatus(str, Enum):
    PENDING = 'pending'
    SENT = 'sent'
    CONFIRMED = 'confirmed'
    REJECTED = 'rejected'
    EXPIRED = 'expired'
    FAILED = 'failed'


class CriticalResultRequest(BaseModel):
    """Запрос на отправку критического результата"""
    ids: int = Field(..., description="IDS пациента")
    department: str = Field(..., description="Отделение")
    test_name: str = Field(..., description="Наименование теста")
    result_value: float = Field(..., description="Значение результата")
    ref_lower: Optional[float] = Field(None, description="Нижняя граница нормы")
    ref_upper: Optional[float] = Field(None, description="Верхняя граница нормы")
    deviation_percent: Optional[float] = Field(None, description="Процент отклонения")
    monitor_type: str = Field('both', description="Тип мониторинга")


class ResultResponse(BaseModel):
    """Ответ с результатом"""
    result_key: str
    ids: int
    department: str
    test_name: str
    result_value: float
    status: str
    created_at: datetime


class ConfirmationRequest(BaseModel):
    """Запрос на подтверждение"""
    result_keys: List[str] = Field(..., description="Список ключей результатов")


class UserRequest(BaseModel):
    """Запрос на добавление пользователя"""
    user_id: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None


class UserResponse(BaseModel):
    """Ответ с информацией о пользователе"""
    user_id: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    is_active: bool = True


# RabbitMQ сообщения
class ResultMessage(BaseModel):
    """Сообщение с результатом"""
    result_id: int
    result_key: str
    ids: int
    department: str
    test_name: str
    result_value: float
    ref_lower: Optional[float] = None
    ref_upper: Optional[float] = None
    deviation_percent: Optional[float] = None
    monitor_type: str = 'both'
    status: str = 'pending'
    created_at: str
    attempts: int = 0


class UserResponseMessage(BaseModel):
    """Ответ пользователя"""
    result_id: int
    result_key: str
    action: str  # 'approved' или 'rejected'
    user_id: str
    username: Optional[str] = None
    timestamp: str


class ConfirmationResultMessage(BaseModel):
    """Подтверждение для десктопа"""
    result_id: int
    result_key: str
    action: str
    confirmed_by: str
    confirmed_at: str