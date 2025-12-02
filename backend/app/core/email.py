import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from backend.app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Служба отправки почты"""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"  # Пример: Gmail SMTP
        self.smtp_port = 587
        self.sender_email = "noreply@yourapp.com"
        self.sender_password = "your-email-password"
        
    async def send_otp_email(self, recipient_email: str, otp_code: str) -> bool:
        """
        Отправить сообщение с кодом аутентификации OTP
        
        Args:
            recipient_email: Почтовый ящик получателя
            otp_code: 6 - битный код проверки
            
        Returns:
            bool: Удалось ли отправить
        """
        try:
            # Подключается к реальному SMTP - серверу.
            # Для демонстрации мы печатаем только содержимое почты
            
            subject = "Ваш код проверки - платформа Ecommerce"
            
            # Создание содержимого HTML - почты
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .otp-code {{ 
                        font-size: 32px; 
                        font-weight: bold; 
                        color: #2c3e50; 
                        text-align: center; 
                        margin: 30px 0; 
                        padding: 20px;
                        background-color: #f8f9fa;
                        border-radius: 8px;
                        letter-spacing: 10px;
                    }}
                    .footer {{ 
                        margin-top: 40px; 
                        padding-top: 20px; 
                        border-top: 1px solid #eee; 
                        color: #666; 
                        font-size: 12px; 
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Ecommerce平台</h1>
                    </div>
                    
                    <h2>Проверьте свой почтовый ящик</h2>
                    <p>Здравствуйте！</p>
                    <p>Вы пытаетесь войти в систему или зарегистрироваться на платформе Ecommerce, введите следующий код проверки для завершения проверки:</p>
                    
                    <div class="otp-code">{otp_code}</div>
                    
                    <p><strong>Этот код проверки истекает через 10 минут.</strong></p>
                    <p>Если вы не запросили этот код проверки, игнорируйте это сообщение.</p>
                    
                    <div class="footer">
                        <p>Это сообщение отправляется системой автоматически, не отвечайте.</p>
                        <p>©  Платформа Ecommerce 2024. Все права сохраняются.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # В реальном проекте, здесь будет отправлена почта
            # Печать сообщений для отладки
            logger.info(f"Готовьтесь отправить OTP - почту: {recipient_email}")
            logger.info(f"Почтовая тема: {subject}")
            logger.info(f"капча: {otp_code}")
            
            # Задержка отправки аналоговой почты
            import asyncio
            await asyncio.sleep(1)  # Задержка аналоговой сети
            
            logger.info(f"Почта OTP отправлена: {recipient_email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {str(e)}")
            return False
    
    async def send_welcome_email(self, recipient_email: str, user_name: Optional[str] = None) -> bool:
        """Отправить приветственное письмо"""
        try:
            subject = "Добро пожаловать на платформу Ecommerce"
            greeting = f"Уважаемый {user_name}, "if user_name else" Здравствуйте,"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .welcome {{ text-align: center; margin: 40px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="welcome">
                        <h1>🎉 Добро пожаловать.！</h1>
                    </div>
                    
                    <p>{greeting}</p>
                    <p>Спасибо за регистрацию на платформе Ecommerce! Ваш аккаунт был успешно создан.</p>
                    <p>Теперь вы можете начать создавать или управлять своим магазином.</p>
                    
                    <p>Если у вас есть вопросы, пожалуйста, свяжитесь с нами в любое время.</p>
                    
                    <p>Приятного использования.！</p>
                    <p><strong>Команда платформы Ecommerce</strong></p>
                </div>
            </body>
            </html>
            """
            
            logger.info(f"Отправить приветственное письмо: {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки приветственного сообщения: {str(e)}")
            return False


# Создание примеров глобальной почтовой службы
email_service = EmailService()