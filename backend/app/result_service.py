# result_service.py
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from .database import (
    AnonymizedResult, MobileUser, NotificationLog,
    get_db_session, get_result_by_key, get_result_by_id
)
from .models import ResultStatus

logger = logging.getLogger(__name__)


class ResultService:
    """Сервис для работы с результатами"""

    def __init__(self, db: Session = None):
        self.db = db or get_db_session()
        self._own_session = db is None

    def close(self):
        if self._own_session and self.db:
            self.db.close()

    def create_result(self, data: Dict[str, Any]) -> AnonymizedResult:
        result_key = str(uuid.uuid4())

        result = AnonymizedResult(
            result_key=result_key,
            ids=data.get('ids'),
            department=data.get('department'),
            test_name=data.get('test_name'),
            result_value=data.get('result_value'),
            ref_lower=data.get('ref_lower'),
            ref_upper=data.get('ref_upper'),
            deviation_percent=data.get('deviation_percent'),
            monitor_type=data.get('monitor_type', 'both'),
            status=ResultStatus.PENDING.value,
            acknowledged=False,
            attempts_count=0
        )

        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)

        logger.info(f"Created result: {result_key} (IDS: {data.get('ids')})")
        return result

    def get_pending_results(self) -> List[AnonymizedResult]:
        return self.db.query(AnonymizedResult).filter(
            AnonymizedResult.status == ResultStatus.PENDING.value
        ).all()

    def get_pending_grouped(self) -> Dict[str, List[AnonymizedResult]]:
        pending = self.get_pending_results()
        grouped = {}
        for r in pending:
            key = f"{r.ids}|{r.department}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(r)
        return grouped

    def mark_as_sent(self, result_id: int, user_id: str, message_id: str) -> bool:
        result = get_result_by_id(self.db, result_id)
        if result:
            result.status = ResultStatus.SENT.value
            result.mobile_user_id = user_id
            result.push_message_id = message_id
            result.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def mark_as_confirmed(self, result_id: int, user_id: str) -> bool:
        result = get_result_by_id(self.db, result_id)
        if result:
            result.status = ResultStatus.CONFIRMED.value
            result.confirmed_at = datetime.utcnow()
            result.confirmed_by = user_id
            result.updated_at = datetime.utcnow()
            self.db.commit()
            self._add_log(result_id, result.result_key, user_id, 'confirmed')
            return True
        return False

    def mark_as_rejected(self, result_id: int, user_id: str, reason: str = None) -> bool:
        result = get_result_by_id(self.db, result_id)
        if result:
            result.status = ResultStatus.REJECTED.value
            result.confirmed_at = datetime.utcnow()
            result.confirmed_by = user_id
            result.rejection_reason = reason
            result.updated_at = datetime.utcnow()
            self.db.commit()
            self._add_log(result_id, result.result_key, user_id, 'rejected', reason)
            return True
        return False

    def mark_as_expired(self, result_id: int) -> bool:
        result = get_result_by_id(self.db, result_id)
        if result:
            result.status = ResultStatus.EXPIRED.value
            result.updated_at = datetime.utcnow()
            self.db.commit()
            self._add_log(result_id, result.result_key, None, 'expired')
            return True
        return False

    def mark_as_acknowledged(self, result_key: str) -> bool:
        result = get_result_by_key(self.db, result_key)
        if result:
            result.acknowledged = True
            result.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def get_confirmed_results(self) -> List[AnonymizedResult]:
        return self.db.query(AnonymizedResult).filter(
            AnonymizedResult.status == ResultStatus.CONFIRMED.value,
            AnonymizedResult.acknowledged == False
        ).all()

    def delete_result(self, result_key: str) -> bool:
        try:
            self.db.query(NotificationLog).filter(
                NotificationLog.result_key == result_key
            ).delete()

            result = get_result_by_key(self.db, result_key)
            if result:
                self.db.delete(result)
                self.db.commit()
                logger.info(f"Result deleted: {result_key}")
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting result: {e}")
            return False

    def get_active_users(self) -> List[MobileUser]:
        return self.db.query(MobileUser).filter(
            MobileUser.is_active == True
        ).all()

    def get_user_by_user_id(self, user_id: str) -> Optional[MobileUser]:
        return self.db.query(MobileUser).filter(
            MobileUser.user_id == user_id
        ).first()

    def _add_log(self, result_id: int, result_key: str, user_id: str,
                 action: str, details: str = None):
        log = NotificationLog(
            result_id=result_id,
            result_key=result_key,
            user_id=user_id,
            action=action,
            details=details,
        )
        self.db.add(log)
        self.db.commit()

    def get_statistics(self) -> Dict[str, Any]:
        total = self.db.query(AnonymizedResult).count()
        pending = self.db.query(AnonymizedResult).filter(
            AnonymizedResult.status == ResultStatus.PENDING.value
        ).count()
        sent = self.db.query(AnonymizedResult).filter(
            AnonymizedResult.status == ResultStatus.SENT.value
        ).count()
        confirmed = self.db.query(AnonymizedResult).filter(
            AnonymizedResult.status == ResultStatus.CONFIRMED.value
        ).count()
        rejected = self.db.query(AnonymizedResult).filter(
            AnonymizedResult.status == ResultStatus.REJECTED.value
        ).count()
        expired = self.db.query(AnonymizedResult).filter(
            AnonymizedResult.status == ResultStatus.EXPIRED.value
        ).count()
        acknowledged = self.db.query(AnonymizedResult).filter(
            AnonymizedResult.acknowledged == True
        ).count()

        total_users = self.db.query(MobileUser).count()
        active_users = self.db.query(MobileUser).filter(
            MobileUser.is_active == True
        ).count()

        return {
            'results': {
                'total': total,
                'pending': pending,
                'sent': sent,
                'confirmed': confirmed,
                'rejected': rejected,
                'expired': expired,
                'acknowledged': acknowledged,
            },
            'users': {
                'total': total_users,
                'active': active_users,
            }
        }