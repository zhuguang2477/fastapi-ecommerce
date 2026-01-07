# backend/app/core/email.py
"""
邮件发送模块 - 支持SSL和TLS连接
"""
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import aiosmtplib
import asyncio
import time

from .config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Класс почтового сервиса - поддерживает SSL/TLS соединения"""
    
    def __init__(self):
        # Конфигурация Gmail SMTP
        self.smtp_host = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 465)
        self.smtp_user = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.use_tls = getattr(settings, 'SMTP_TLS', True)
        self.from_email = getattr(settings, 'SENDER_EMAIL', '')
        self.from_name = getattr(settings, 'EMAILS_FROM_NAME', 'FastAPI E-commerce платформа')
        
        # Параметры подключения
        self.max_retries = 3
        self.retry_delay = 2
        
        # Валидация конфигурации
        self._validate_config()
    
    def _validate_config(self):
        """Проверка конфигурации почты"""
        # Проверка полноты конфигурации
        config_ok = (
            self.smtp_host and
            self.smtp_user and
            self.smtp_password and
            self.from_email and
            self.smtp_password not in ['your-app-password', 'test123', '']
        )
        
        if config_ok:
            self.simulation_mode = False
            logger.info("✅ Конфигурация почты полная, будет использована реальная отправка писем")
            logger.info(f"   SMTP сервер: {self.smtp_host}:{self.smtp_port}")
            logger.info(f"   Отправитель: {self.from_email}")
        else:
            self.simulation_mode = True
            logger.warning("⚠️  Конфигурация почты неполная, используется режим симуляции")
    
    def _create_message(self, email_to: str, subject: str, content: str, content_type: str = "html") -> MIMEMultipart:
        """Создание почтового сообщения"""
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = email_to
        
        # Добавление содержимого
        if content_type == "html":
            part = MIMEText(content, "html", "utf-8")
        else:
            part = MIMEText(content, "plain", "utf-8")
        
        message.attach(part)
        return message
    
    async def send_email_async(
        self,
        email_to: str,
        subject: str,
        content: str,
        content_type: str = "html"
    ) -> bool:
        """Асинхронная отправка письма"""
        # Если режим симуляции, только логируем
        if self.simulation_mode:
            logger.info(f"[Симуляция] Отправка письма на {email_to}")
            logger.info(f"[Симуляция] Тема: {subject}")
            return True
        
        # Механизм повторных попыток
        for attempt in range(self.max_retries):
            try:
                logger.info(f"📤 Попытка отправки письма на {email_to} (попытка {attempt + 1}/{self.max_retries})")
                
                # Создание письма
                message = self._create_message(email_to, subject, content, content_type)
                
                # Выбор способа подключения в зависимости от порта
                if self.smtp_port == 465:
                    # Использование SSL соединения (порт 465)
                    context = ssl.create_default_context()
                    
                    # Использование SMTP_SSL для подключения
                    smtp = aiosmtplib.SMTP(
                        hostname=self.smtp_host,
                        port=self.smtp_port,
                        use_tls=True,
                        tls_context=context
                    )
                    
                    await smtp.connect()
                    # Для SSL соединения не требуется вызов starttls
                    
                elif self.smtp_port == 587:
                    # Использование STARTTLS соединения (порт 587)
                    context = ssl.create_default_context()
                    
                    smtp = aiosmtplib.SMTP(
                        hostname=self.smtp_host,
                        port=self.smtp_port,
                        use_tls=False,
                        tls_context=context
                    )
                    
                    await smtp.connect()
                    await smtp.starttls()
                else:
                    logger.error(f"❌ Неподдерживаемый порт: {self.smtp_port}")
                    return False
                
                # Авторизация и отправка письма
                await smtp.login(self.smtp_user, self.smtp_password)
                await smtp.send_message(message)
                await smtp.quit()
                
                logger.info(f"✅ Письмо успешно отправлено: {email_to}")
                return True
                
            except aiosmtplib.SMTPAuthenticationError as e:
                logger.error(f"❌ Ошибка аутентификации Gmail: {e}")
                logger.error("   Пожалуйста, проверьте правильность пароля приложения Gmail")
                return False
                
            except Exception as e:
                logger.error(f"❌ Ошибка отправки письма (попытка {attempt + 1}): {e}")
                
                if attempt < self.max_retries - 1:
                    logger.info(f"Ожидание {self.retry_delay} секунд перед повторной попыткой...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("Достигнуто максимальное количество попыток, отправка не удалась")
                    # Попытка синхронной отправки как запасной вариант
                    try:
                        logger.info("Попытка синхронной отправки как запасной вариант...")
                        return self.send_email_sync(email_to, subject, content, content_type)
                    except:
                        return False
        
        return False
    
    def send_email_sync(
        self,
        email_to: str,
        subject: str,
        content: str,
        content_type: str = "html"
    ) -> bool:
        """Синхронная отправка письма"""
        # Если режим симуляции, только логируем
        if self.simulation_mode:
            logger.info(f"[Симуляция] Отправка письма на {email_to}")
            logger.info(f"[Симуляция] Тема: {subject}")
            return True
        
        # Механизм повторных попыток
        for attempt in range(self.max_retries):
            try:
                logger.info(f"📤 Синхронная отправка письма на {email_to} (попытка {attempt + 1}/{self.max_retries})")
                
                # Создание письма
                message = self._create_message(email_to, subject, content, content_type)
                
                # Выбор способа подключения в зависимости от порта
                if self.smtp_port == 465:
                    # Использование SSL соединения (порт 465)
                    context = ssl.create_default_context()
                    
                    with smtplib.SMTP_SSL(
                        self.smtp_host, 
                        self.smtp_port, 
                        context=context,
                        timeout=30
                    ) as server:
                        server.login(self.smtp_user, self.smtp_password)
                        server.send_message(message)
                        
                elif self.smtp_port == 587:
                    # Использование STARTTLS соединения (порт 587)
                    context = ssl.create_default_context()
                    
                    with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                        server.ehlo()
                        server.starttls(context=context)
                        server.ehlo()
                        server.login(self.smtp_user, self.smtp_password)
                        server.send_message(message)
                else:
                    logger.error(f"❌ Неподдерживаемый порт: {self.smtp_port}")
                    return False
                
                logger.info(f"✅ Письмо успешно отправлено: {email_to}")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"❌ Ошибка аутентификации Gmail: {e}")
                return False
                
            except Exception as e:
                logger.error(f"❌ Ошибка отправки письма (попытка {attempt + 1}): {e}")
                
                if attempt < self.max_retries - 1:
                    logger.info(f"Ожидание {self.retry_delay} секунд перед повторной попыткой...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Достигнуто максимальное количество попыток, отправка не удалась")
                    return False
        
        return False


# Глобальный экземпляр почтового сервиса
email_service = EmailService()


async def send_email(
    email_to: str,
    subject: str,
    html_content: str = "",
    plain_content: str = "",
    template_name: str = None,
    template_context: Dict[str, Any] = None
) -> bool:
    """Отправка письма (асинхронно)"""
    try:
        # Определение содержимого письма
        if html_content:
            content = html_content
            content_type = "html"
        elif plain_content:
            content = plain_content
            content_type = "plain"
        else:
            logger.error("Содержимое письма пустое")
            return False
        
        # Отправка письма
        return await email_service.send_email_async(
            email_to=email_to,
            subject=subject,
            content=content,
            content_type=content_type
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки письма: {e}")
        return False


def send_email_sync(
    email_to: str,
    subject: str,
    html_content: str = "",
    plain_content: str = "",
    template_name: str = None,
    template_context: Dict[str, Any] = None
) -> bool:
    """Отправка письма (синхронно)"""
    try:
        if html_content:
            content = html_content
            content_type = "html"
        elif plain_content:
            content = plain_content
            content_type = "plain"
        else:
            logger.error("Содержимое письма пустое")
            return False
        
        return email_service.send_email_sync(
            email_to=email_to,
            subject=subject,
            content=content,
            content_type=content_type
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки письма: {e}")
        return False


# Функции для обратной совместимости (обеспечивают совместимость с существующим кодом)
def get_email_service():
    """Получение экземпляра почтового сервиса (функция для совместимости)"""
    class EmailServiceAdapter:
        """Адаптер почтового сервиса для совместимости со старым интерфейсом"""
        
        @staticmethod
        async def send_welcome_email(email: str, username: str) -> bool:
            """Отправка приветственного письма (метод для совместимости)"""
            try:
                from .config import settings
                app_name = getattr(settings, 'APP_NAME', 'FastAPI E-commerce платформа')
                subject = f"Добро пожаловать в {app_name}!"
                
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <body>
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <h2 style="color: #4CAF50;">Добро пожаловать в {app_name}!</h2>
                        <p>Уважаемый(ая) {username}, здравствуйте!</p>
                        <p>Спасибо за регистрацию в {app_name}, мы рады, что вы присоединились к нам.</p>
                        <hr>
                        <p style="color: #777;">Команда {app_name}</p>
                    </div>
                </body>
                </html>
                """
                
                return await send_email(
                    email_to=email,
                    subject=subject,
                    html_content=html_content
                )
                
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке приветственного письма: {e}")
                return False
        
        @staticmethod
        async def send_verification_email(email: str, otp_code: str) -> bool:
            """Отправка письма с подтверждением (метод для совместимости)"""
            try:
                from .config import settings
                app_name = getattr(settings, 'APP_NAME', 'FastAPI E-commerce платформа')
                subject = f"{app_name} - Код подтверждения {otp_code}"
                
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <body>
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <h2 style="color: #4CAF50;">Код подтверждения email</h2>
                        <p>Ваш код подтверждения:</p>
                        <div style="font-size: 32px; font-weight: bold; color: #4CAF50; margin: 20px 0; text-align: center;">
                            {otp_code}
                        </div>
                        <p>Код будет действителен в течение 10 минут, пожалуйста, используйте его как можно скорее.</p>
                        <hr>
                        <p style="color: #777;">{app_name}</p>
                    </div>
                </body>
                </html>
                """
                
                return await send_email(
                    email_to=email,
                    subject=subject,
                    html_content=html_content
                )
                
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке письма с подтверждением: {e}")
                return False
        
        @staticmethod
        async def send_profile_completed_email(email: str, username: str) -> bool:
            """Отправка письма о завершении регистрации профиля"""
            try:
                from .config import settings
                app_name = getattr(settings, 'APP_NAME', 'FastAPI E-commerce платформа')
                subject = f"Регистрация профиля завершена - {app_name}"
                
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            line-height: 1.6;
                            color: #333;
                        }}
                        .container {{
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                            border: 1px solid #ddd;
                            border-radius: 10px;
                        }}
                        .header {{
                            background-color: #4CAF50;
                            color: white;
                            padding: 20px;
                            text-align: center;
                            border-radius: 10px 10px 0 0;
                        }}
                        .content {{
                            padding: 30px;
                        }}
                        .footer {{
                            text-align: center;
                            padding: 20px;
                            color: #777;
                            font-size: 12px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Регистрация завершена!</h1>
                        </div>
                        <div class="content">
                            <p>Уважаемый(ая) {username}, здравствуйте!</p>
                            <p>Мы рады сообщить, что ваш профиль в {app_name} успешно создан и завершен.</p>
                            <p>Теперь вы можете в полной мере использовать все возможности нашей платформы:</p>
                            <ul>
                                <li>Просматривать товары и категории</li>
                                <li>Добавлять товары в избранное</li>
                                <li>Оформлять заказы</li>
                                <li>Отслеживать статус заказов</li>
                                <li>И многое другое!</li>
                            </ul>
                            <p>Если у вас возникнут вопросы, наша служба поддержки всегда готова помочь.</p>
                            <p>С наилучшими пожеланиями,<br>Команда {app_name}</p>
                        </div>
                        <div class="footer">
                            <p>© 2025 {app_name}. Все права защищены.</p>
                            <p>Это автоматическое письмо, пожалуйста, не отвечайте на него.</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                return await send_email(
                    email_to=email,
                    subject=subject,
                    html_content=html_content
                )
                
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке письма о завершении регистрации: {e}")
                return False
    
    return EmailServiceAdapter()