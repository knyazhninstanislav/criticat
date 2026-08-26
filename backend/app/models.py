from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

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
    chat_id: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None

class UserResponse(BaseModel):
    """Ответ с информацией о пользователе"""
    chat_id: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    is_active: bool = True