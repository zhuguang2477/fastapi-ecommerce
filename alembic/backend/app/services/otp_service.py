# backend/app/services/otp_service.py
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import random

from backend.app.models.otp import OTP
from backend.app.core.config import settings
from backend.app.core.cache import cache_service

logger = logging.getLogger(__name__)

class OTPService:
    """Улучшенный OTP сервис"""
    
    @staticmethod
    def can_send_otp(email: str, ip_address: str, db: Session) -> bool:
        """Проверить возможность отправки OTP (ограничение частоты)"""
        try:
            # 1. Ограничение частоты по IP-адресу
            ip_key = f"otp_ip_limit:{ip_address}"
            ip_count = cache_service.redis.get(ip_key) or 0
            
            if int(ip_count) >= 10:  # Максимум 10 раз в день с одного IP
                logger.warning(f"Ограничение частоты по IP: {ip_address}")
                return False
            
            # 2. Ограничение частоты по email
            email_key = f"otp_email_limit:{email}"
            email_count = cache_service.redis.get(email_key) or 0
            
            if int(email_count) >= 5:  # Максимум 5 раз в час для одного email
                logger.warning(f"Ограничение частоты по email: {email}")
                return False
            
            # 3. Проверить, не отправлялся ли OTP недавно (в течение 1 минуты)
            last_otp = db.query(OTP).filter(
                and_(
                    OTP.email == email,
                    OTP.created_at >= datetime.utcnow() - timedelta(minutes=1)
                )
            ).first()
            
            if last_otp:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки частоты отправки OTP: {e}")
            return True  # В случае ошибки ослабить ограничения
    
    @staticmethod
    def verify_otp(email: str, otp_code: str, ip_address: str, db: Session) -> OTP:
        """Проверить OTP код, включает проверку безопасности"""
        try:
            # 1. Проверить ограничение количества попыток
            attempt_key = f"otp_attempts:{ip_address}:{email}"
            attempts = cache_service.redis.get(attempt_key) or 0
            
            if int(attempts) >= 5:  # Максимум 5 попыток
                logger.warning(f"Превышено количество попыток OTP: {email} от {ip_address}")
                return None
            
            # 2. Найти действительный OTP
            now = datetime.utcnow()
            otp_record = db.query(OTP).filter(
                and_(
                    OTP.email == email,
                    OTP.otp_code == otp_code,
                    OTP.is_used == False,
                    OTP.expires_at > now,
                    OTP.created_at >= now - timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
                )
            ).first()
            
            # 3. Записать количество попыток
            if otp_record:
                cache_service.redis.delete(attempt_key)  # Успешная проверка, очистить счетчик
            else:
                # Неудачная проверка, увеличить счетчик
                cache_service.redis.incr(attempt_key)
                cache_service.redis.expire(attempt_key, 3600)  # Истечет через 1 час
            
            return otp_record
            
        except Exception as e:
            logger.error(f"Ошибка проверки OTP: {e}")
            return None
    
    @staticmethod
    def mark_otp_used(otp_id: int, db: Session) -> bool:
        """Пометить OTP как использованный по ID"""
        try:
            otp_record = db.query(OTP).filter(OTP.id == otp_id).first()
            if not otp_record:
                logger.error(f"OTP с ID {otp_id} не найден")
                return False
            
            otp_record.is_used = True
            otp_record.used_at = datetime.utcnow()
            db.commit()
            logger.info(f"OTP {otp_id} отмечен как использованный для {otp_record.email}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при отметке OTP {otp_id} как использованного: {e}")
            return False
    
    @staticmethod
    def mark_otp_used_by_record(otp_record: OTP, db: Session) -> bool:
        """Пометить OTP как использованный (по объекту OTP)"""
        try:
            otp_record.is_used = True
            otp_record.used_at = datetime.utcnow()
            db.commit()
            logger.info(f"OTP {otp_record.id} отмечен как использованный для {otp_record.email}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при отметке OTP как использованного: {e}")
            return False
    
    @staticmethod
    def get_last_otp(email: str, db: Session) -> OTP:
        """Получить последний отправленный OTP для email"""
        try:
            otp_record = db.query(OTP).filter(
                OTP.email == email
            ).order_by(OTP.created_at.desc()).first()
            return otp_record
        except Exception as e:
            logger.error(f"Ошибка получения последнего OTP для {email}: {e}")
            return None
    
    @staticmethod
    def clean_expired_otps(db: Session, hours: int = 24) -> int:
        """Очистить истекшие OTP записи"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            expired_count = db.query(OTP).filter(
                OTP.created_at < cutoff_time
            ).delete()
            db.commit()
            logger.info(f"Удалено {expired_count} истекших OTP записей")
            return expired_count
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при очистке истекших OTP: {e}")
            return 0
    
    @staticmethod
    async def send_otp_email(email: str, ip_address: str, db: Session) -> bool:
        """Отправить OTP по электронной почте, включает запись безопасности"""
        try:
            # Сгенерировать OTP код
            otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Установить время истечения
            expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
            
            # Создать запись OTP
            otp_record = OTP(
                email=email,
                otp_code=otp_code,
                is_used=False,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=None  # Можно получить из заголовков запроса
            )
            
            db.add(otp_record)
            db.commit()
            
            # Обновить счетчики ограничения частоты
            ip_key = f"otp_ip_limit:{ip_address}"
            email_key = f"otp_email_limit:{email}"
            
            # Установить истечение через 24 часа
            cache_service.redis.incr(ip_key)
            cache_service.redis.expire(ip_key, 86400)
            
            # Установить истечение через 1 час
            cache_service.redis.incr(email_key)
            cache_service.redis.expire(email_key, 3600)
            
            # Отправить email
            from backend.app.core.email import get_email_service
            email_service = get_email_service()
            
            return await email_service.send_verification_email(email, otp_code)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка отправки OTP по электронной почте: {e}")
            return False