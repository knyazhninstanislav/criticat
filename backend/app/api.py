from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging
import uuid
from datetime import datetime
import json

from .config import settings
from .database import SessionLocal, AnonymizedResult, TelegramUser, NotificationLog, get_db
from .models import CriticalResultRequest, ResultResponse, ConfirmationRequest, UserRequest, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/results", response_model=ResultResponse)
async def receive_result(result: CriticalResultRequest):
    """Получение обезличенного результата от десктопа"""
    db = SessionLocal()
    try:
        result_key = str(uuid.uuid4())
        
        db_result = AnonymizedResult(
            result_key=result_key,
            ids=result.ids,
            department=result.department,
            test_name=result.test_name,
            result_value=result.result_value,
            ref_lower=result.ref_lower,
            ref_upper=result.ref_upper,
            deviation_percent=result.deviation_percent,
            monitor_type=result.monitor_type,
            status='pending'
        )
        
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        
        logger.info(f"Получен результат: {result_key} (IDS: {result.ids}, {result.test_name})")
        
        return ResultResponse(
            result_key=result_key,
            ids=result.ids,
            department=result.department,
            test_name=result.test_name,
            result_value=result.result_value,
            status='pending',
            created_at=db_result.created_at
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка сохранения результата: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/results/confirm", response_model=dict)
async def confirm_results(confirmation: ConfirmationRequest):
    """Подтверждение результатов"""
    db = SessionLocal()
    try:
        confirmed_keys = []
        
        for key in confirmation.result_keys:
            result = db.query(AnonymizedResult).filter(
                AnonymizedResult.result_key == key
            ).first()
            
            if result:
                result.status = 'confirmed'
                result.confirmed_at = datetime.utcnow()
                confirmed_keys.append(key)
        
        db.commit()
        
        logger.info(f"Подтверждены результаты: {confirmed_keys}")
        
        return {
            'success': True,
            'confirmed': confirmed_keys
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка подтверждения: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/results/pending", response_model=List[ResultResponse])
async def get_pending_results():
    """Получение ожидающих результатов"""
    db = SessionLocal()
    try:
        results = db.query(AnonymizedResult).filter(
            AnonymizedResult.status == 'pending'
        ).all()
        
        return [
            ResultResponse(
                result_key=r.result_key,
                ids=r.ids,
                department=r.department,
                test_name=r.test_name,
                result_value=r.result_value,
                status=r.status,
                created_at=r.created_at
            ) for r in results
        ]
    finally:
        db.close()

@router.get("/results/confirmed", response_model=List[ResultResponse])
async def get_confirmed_results():
    """Получение подтвержденных результатов"""
    db = SessionLocal()
    try:
        results = db.query(AnonymizedResult).filter(
            AnonymizedResult.status == 'confirmed'
        ).all()
        
        return [
            ResultResponse(
                result_key=r.result_key,
                ids=r.ids,
                department=r.department,
                test_name=r.test_name,
                result_value=r.result_value,
                status=r.status,
                created_at=r.created_at
            ) for r in results
        ]
    finally:
        db.close()

@router.get("/results/all", response_model=List[ResultResponse])
async def get_all_results():
    """Получение всех результатов"""
    db = SessionLocal()
    try:
        results = db.query(AnonymizedResult).order_by(
            AnonymizedResult.created_at.desc()
        ).all()
        
        return [
            ResultResponse(
                result_key=r.result_key,
                ids=r.ids,
                department=r.department,
                test_name=r.test_name,
                result_value=r.result_value,
                status=r.status,
                created_at=r.created_at
            ) for r in results
        ]
    finally:
        db.close()

@router.post("/users", response_model=UserResponse)
async def add_user(user: UserRequest):
    """Добавление пользователя"""
    db = SessionLocal()
    try:
        db_user = TelegramUser(
            chat_id=user.chat_id,
            username=user.username,
            full_name=user.full_name,
            department=user.department
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return UserResponse(
            chat_id=db_user.chat_id,
            username=db_user.username,
            full_name=db_user.full_name,
            department=db_user.department,
            is_active=db_user.is_active
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка добавления пользователя: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/users", response_model=List[UserResponse])
async def get_users():
    """Получение списка пользователей"""
    db = SessionLocal()
    try:
        users = db.query(TelegramUser).filter(
            TelegramUser.is_active == True
        ).all()
        
        return [
            UserResponse(
                chat_id=u.chat_id,
                username=u.username,
                full_name=u.full_name,
                department=u.department,
                is_active=u.is_active
            ) for u in users
        ]
    finally:
        db.close()

@router.delete("/users/{chat_id}")
async def delete_user(chat_id: str):
    """Удаление пользователя"""
    db = SessionLocal()
    try:
        user = db.query(TelegramUser).filter(
            TelegramUser.chat_id == chat_id
        ).first()
        
        if user:
            user.is_active = False
            db.commit()
            return {'success': True, 'message': 'Пользователь деактивирован'}
        
        return {'success': False, 'message': 'Пользователь не найден'}
    finally:
        db.close()