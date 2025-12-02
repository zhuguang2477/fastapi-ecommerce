# backend/app/services/otp_service.py
import random
import string
from datetime import datetime, timedelta
from typing import Optional
import logging
from backend.app.redis_client import get_redis
from backend.app.core.email import EmailService

logger = logging.getLogger(__name__)


class OTPService:
    """Услуги OTP"""
    
    OTP_EXPIRE_MINUTES = 10  # Срок действия OTP 10 минут.
    
    @staticmethod
    def generate_otp_code(length: int = 6) -> str:
        """Создание 6 - битного цифрового OTP - кода"""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    async def send_otp_email(email: str) -> bool:
        """
        Отправить OTP - почту
        
        Args:
            email: Почтовый ящик
            
        Returns:
            bool: Успешно ли
        """
        try:
            # Создание OTP
            otp_code = OTPService.generate_otp_code()
            
            # Сохранить в Redis, установив время истечения срока действия
            redis_client = get_redis()
            redis_key = f"otp:{email}"
            redis_client.setex(redis_key, OTPService.OTP_EXPIRE_MINUTES * 60, otp_code)
            
            # Отправить письмо
            # TODO: Настройка реальной почтовой службы в реальном проекте
            email_service = EmailService()
            success = await email_service.send_otp_email(email, otp_code)
            
            if success:
                logger.info(f"OTP sent to {email}: {otp_code}")
                # Среда разработки: Печать OTP на консоль
                print(f"📧 OTP for {email}: {otp_code}")
                return True
            else:
                logger.error(f"Failed to send OTP email to {email}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending OTP to {email}: {e}")
            return False
    
    @staticmethod
    def verify_otp(email: str, otp_code: str) -> bool:
        """
        Проверить код OTP
        
        Args:
            email: Почтовый ящик пользователя
            otp_code: Код OTP, введенный пользователем
            
        Returns:
            bool: Проверить успех
        """
        try:
            redis_client = get_redis()
            redis_key = f"otp:{email}"
            
            # Получить OTP от Redis
            stored_otp = redis_client.get(redis_key)
            
            if not stored_otp:
                logger.warning(f"No OTP found for {email}")
                return False
            
            if stored_otp != otp_code:
                logger.warning(f"Invalid OTP for {email}: expected {stored_otp}, got {otp_code}")
                return False
            
            # Успешная проверка, удаление OTP
            redis_client.delete(redis_key)
            logger.info(f"OTP verified for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying OTP for {email}: {e}")
            return False
    
    @staticmethod
    def cleanup_expired_otps():
        """Очистить устаревший OTP"""
        # Редис автоматически очищает устаревшие ключи
        pass