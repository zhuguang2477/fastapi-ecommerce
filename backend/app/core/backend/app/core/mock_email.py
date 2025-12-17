# backend/app/core/mock_email.py
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class MockEmailService:
    """Мок-сервис электронной почты для среды разработки"""
    
    def __init__(self):
        logger.info("Инициализация мок-сервиса электронной почты (среда разработки)")
    
    async def send_verification_email(self, to_email: str, otp_code: str):
        """Мок отправки письма с верификацией"""
        logger.info(f"[Mock Email] Отправка письма с кодом верификации на {to_email}")
        logger.info(f"[Mock Email] Код верификации: {otp_code}")
        logger.info(f"[Mock Email] В рабочей среде будет отправлено настоящее письмо")
        return True
    
    async def send_welcome_email(self, to_email: str, username: str):
        """Мок отправки приветственного письма"""
        logger.info(f"[Mock Email] Отправка приветственного письма на {to_email}")
        logger.info(f"[Mock Email] Имя пользователя: {username}")
        return True