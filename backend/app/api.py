# api.py
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
import logging
import uuid
from datetime import datetime, timedelta

from .config import settings
from .rabbitmq_client import rabbitmq_client
from .database import SessionLocal, AnonymizedResult, TelegramUser, NotificationLog
from .models import (
    CriticalResultRequest, ResultResponse, ConfirmationRequest,
    UserRequest, UserResponse, ResultMessage
)
from .result_service import ResultService

logger = logging.getLogger(__name__)

router = APIRouter()


def verify_api_key(x_api_key: str = Header(None), authorization: str = Header(None)):
    """Проверка API ключа"""
    api_key = x_api_key

    if not api_key and authorization:
        if authorization.startswith('Bearer '):
            api_key = authorization[7:]

    if settings.api_key and api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Неверный API ключ")

    return True


# ========== АВТОРИЗАЦИЯ ==========

@router.get("/auth/verify", response_model=dict)
async def verify_auth(api_key_valid: bool = Depends(verify_api_key)):
    """Проверка авторизации"""
    return {
        'success': True,
        'message': 'Авторизация успешна',
        'timestamp': datetime.utcnow().isoformat()
    }


# ========== РЕЗУЛЬТАТЫ ==========

@router.post("/results", response_model=dict)
async def receive_result(data: dict, api_key_valid: bool = Depends(verify_api_key)):
    """Получение результата от десктопа"""
    try:
        service = ResultService()

        # Сохраняем результат в БД
        result = service.create_result(data)

        # Отправляем в RabbitMQ для обработки
        result_data = {
            'result_id': result.id,
            'result_key': result.result_key,
            'ids': result.ids,
            'department': result.department,
            'test_name': result.test_name,
            'result_value': result.result_value,
            'ref_lower': result.ref_lower,
            'ref_upper': result.ref_upper,
            'deviation_percent': result.deviation_percent,
            'monitor_type': result.monitor_type,
            'status': result.status,
            'created_at': result.created_at.isoformat(),
            'attempts': 0
        }

        # Публикуем в очередь входящих результатов
        await rabbitmq_client.publish('lab.results.raw', result_data)

        service.close()

        logger.info(f"Получен результат: {result.result_key} (IDS: {data.get('ids')})")

        return {
            'success': True,
            'result_key': result.result_key,
            'message': 'Результат принят в обработку'
        }

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/confirmed", response_model=dict)
async def get_confirmed_results(api_key_valid: bool = Depends(verify_api_key)):
    """Получение подтвержденных результатов"""
    service = ResultService()
    try:
        results = service.get_confirmed_results()

        result_list = []
        for r in results:
            result_list.append({
                'result_key': r.result_key,
                'ids': r.ids,
                'department': r.department,
                'test_name': r.test_name,
                'result_value': r.result_value,
                'confirmed_at': r.confirmed_at.isoformat() if r.confirmed_at else None,
                'confirmed_by': r.confirmed_by,
            })

        return {'success': True, 'results': result_list}
    finally:
        service.close()


@router.get("/results/all", response_model=dict)
async def get_all_results(api_key_valid: bool = Depends(verify_api_key)):
    """Получение всех результатов"""
    service = ResultService()
    try:
        results = service.db.query(AnonymizedResult).order_by(
            AnonymizedResult.created_at.desc()
        ).all()

        result_list = []
        for r in results:
            result_list.append({
                'result_key': r.result_key,
                'ids': r.ids,
                'department': r.department,
                'test_name': r.test_name,
                'result_value': r.result_value,
                'status': r.status,
                'created_at': r.created_at.isoformat() if r.created_at else None,
            })

        return {'success': True, 'results': result_list}
    finally:
        service.close()


@router.post("/results/acknowledge", response_model=dict)
async def acknowledge_results(data: dict, api_key_valid: bool = Depends(verify_api_key)):
    """Десктоп подтвердил получение"""
    service = ResultService()
    try:
        result_keys = data.get('result_keys', [])
        deleted_count = 0

        for key in result_keys:
            if service.delete_result(key):
                deleted_count += 1

        return {
            'success': True,
            'message': f'Удалено результатов: {deleted_count}',
            'deleted_count': deleted_count
        }
    except Exception as e:
        logger.error(f"Ошибка удаления: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        service.close()


@router.delete("/results/{result_key}", response_model=dict)
async def delete_single_result(result_key: str, api_key_valid: bool = Depends(verify_api_key)):
    """Удаление одного результата"""
    service = ResultService()
    try:
        if service.delete_result(result_key):
            return {'success': True, 'message': 'Результат удален'}
        return {'success': False, 'message': 'Результат не найден'}
    finally:
        service.close()


@router.post("/results/cleanup", response_model=dict)
async def cleanup_old_results(api_key_valid: bool = Depends(verify_api_key)):
    """Очистка старых результатов"""
    service = ResultService()
    try:
        cutoff = datetime.utcnow() - timedelta(days=7)

        old_results = service.db.query(AnonymizedResult).filter(
            AnonymizedResult.created_at < cutoff,
            AnonymizedResult.status.in_(['confirmed', 'rejected', 'expired'])
        ).all()

        deleted_count = 0
        for result in old_results:
            if service.delete_result(result.result_key):
                deleted_count += 1

        return {
            'success': True,
            'message': f'Удалено старых результатов: {deleted_count}',
            'deleted_count': deleted_count
        }
    finally:
        service.close()


# ========== ПОЛЬЗОВАТЕЛИ ==========

@router.get("/users", response_model=dict)
async def get_users(api_key_valid: bool = Depends(verify_api_key)):
    """Получение списка всех пользователей"""
    service = ResultService()
    try:
        users = service.db.query(TelegramUser).all()

        user_list = []
        for u in users:
            user_list.append({
                'chat_id': u.chat_id,
                'username': u.username,
                'full_name': u.full_name,
                'department': u.department,
                'is_active': u.is_active,
                'created_at': u.created_at.isoformat() if u.created_at else None,
            })

        return {'success': True, 'users': user_list}
    finally:
        service.close()


@router.get("/users/active", response_model=dict)
async def get_active_users(api_key_valid: bool = Depends(verify_api_key)):
    """Получение активных пользователей"""
    service = ResultService()
    try:
        users = service.get_active_users()

        user_list = []
        for u in users:
            user_list.append({
                'chat_id': u.chat_id,
                'username': u.username,
                'full_name': u.full_name,
                'department': u.department,
            })

        return {'success': True, 'users': user_list}
    finally:
        service.close()


@router.post("/users", response_model=dict)
async def add_user(data: dict, api_key_valid: bool = Depends(verify_api_key)):
    """Добавление нового пользователя"""
    service = ResultService()
    try:
        chat_id = data.get('chat_id')
        if not chat_id:
            raise HTTPException(status_code=400, detail="chat_id обязателен")

        # Проверяем существование
        existing = service.get_user_by_chat_id(chat_id)

        if existing:
            existing.username = data.get('username', existing.username)
            existing.full_name = data.get('full_name', existing.full_name)
            existing.department = data.get('department', existing.department)
            existing.is_active = True
            service.db.commit()

            return {
                'success': True,
                'message': 'Пользователь обновлен',
                'user': {
                    'chat_id': existing.chat_id,
                    'username': existing.username,
                    'full_name': existing.full_name,
                    'department': existing.department,
                    'is_active': existing.is_active,
                }
            }

        # Создаем нового
        user = TelegramUser(
            chat_id=chat_id,
            username=data.get('username', ''),
            full_name=data.get('full_name', ''),
            department=data.get('department', ''),
            is_active=True
        )
        service.db.add(user)
        service.db.commit()
        service.db.refresh(user)

        logger.info(f"Пользователь добавлен: {chat_id}")

        return {
            'success': True,
            'message': 'Пользователь добавлен',
            'user': {
                'chat_id': user.chat_id,
                'username': user.username,
                'full_name': user.full_name,
                'department': user.department,
                'is_active': user.is_active,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        service.db.rollback()
        logger.error(f"Ошибка добавления: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        service.close()


@router.delete("/users/{chat_id}", response_model=dict)
async def delete_user(chat_id: str, api_key_valid: bool = Depends(verify_api_key)):
    """Деактивация пользователя"""
    service = ResultService()
    try:
        user = service.get_user_by_chat_id(chat_id)

        if user:
            user.is_active = False
            service.db.commit()
            logger.info(f"Пользователь деактивирован: {chat_id}")
            return {'success': True, 'message': 'Пользователь деактивирован'}

        return {'success': False, 'message': 'Пользователь не найден'}
    finally:
        service.close()


@router.put("/users/{chat_id}", response_model=dict)
async def update_user(chat_id: str, data: dict, api_key_valid: bool = Depends(verify_api_key)):
    """Обновление пользователя"""
    service = ResultService()
    try:
        user = service.get_user_by_chat_id(chat_id)

        if not user:
            return {'success': False, 'message': 'Пользователь не найден'}

        if 'username' in data:
            user.username = data['username']
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'department' in data:
            user.department = data['department']
        if 'is_active' in data:
            user.is_active = data['is_active']

        service.db.commit()

        return {
            'success': True,
            'message': 'Пользователь обновлен',
            'user': {
                'chat_id': user.chat_id,
                'username': user.username,
                'full_name': user.full_name,
                'department': user.department,
                'is_active': user.is_active,
            }
        }
    finally:
        service.close()


# ========== СТАТИСТИКА ==========

@router.get("/statistics", response_model=dict)
async def get_statistics(api_key_valid: bool = Depends(verify_api_key)):
    """Получение статистики"""
    service = ResultService()
    try:
        stats = service.get_statistics()
        return {'success': True, 'statistics': stats}
    finally:
        service.close()