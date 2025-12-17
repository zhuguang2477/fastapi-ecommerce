# backend/app/services/otp_service.py
"""
OTP服务模块 - 使用真实Gmail邮件发送
"""
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.core.email import send_email
from backend.app.core.config import settings
from backend.app.models.otp import OTP

logger = logging.getLogger(__name__)


class OTPService:
    """Класс сервиса OTP"""
    
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Генерирует цифровой код подтверждения"""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    async def send_otp_email(email: str, db: Session) -> bool:
        """Отправляет OTP код на email (используя Gmail SMTP)"""
        try:
            # Генерация OTP
            otp_code = OTPService.generate_otp()
            
            # Получение названия приложения
            app_name = getattr(settings, 'APP_NAME', 'FastAPI E-commerce платформа')
            
            # Использование шаблона темы письма из настроек
            subject_template = getattr(settings, 'EMAIL_VERIFICATION_SUBJECT', 'Ваш код подтверждения - {app_name}')
            subject = subject_template.format(app_name=app_name)
            
            # Создание профессионального HTML-содержимого письма
            html_content = f"""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Код подтверждения - {app_name}</title>
                <style>
                    body {{
                        font-family: 'Arial', sans-serif;
                        line-height: 1.6;
                        color: #333;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                        color: white;
                        padding: 30px 20px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 24px;
                        font-weight: 600;
                    }}
                    .content {{
                        padding: 40px 30px;
                    }}
                    .otp-box {{
                        background-color: #f8f9fa;
                        border-radius: 8px;
                        padding: 30px;
                        margin: 30px 0;
                        text-align: center;
                        border: 2px dashed #dee2e6;
                    }}
                    .otp-code {{
                        font-size: 42px;
                        font-weight: bold;
                        color: #4CAF50;
                        letter-spacing: 8px;
                        margin: 20px 0;
                        font-family: 'Courier New', monospace;
                    }}
                    .warning {{
                        color: #e74c3c;
                        font-weight: 500;
                        margin-top: 15px;
                    }}
                    .instructions {{
                        background-color: #e8f4fd;
                        border-left: 4px solid #3498db;
                        padding: 15px;
                        margin: 25px 0;
                        border-radius: 0 5px 5px 0;
                    }}
                    .footer {{
                        text-align: center;
                        padding: 25px;
                        background-color: #f8f9fa;
                        color: #6c757d;
                        font-size: 13px;
                        border-top: 1px solid #e9ecef;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{app_name}</h1>
                        <p>Код подтверждения email</p>
                    </div>
                    
                    <div class="content">
                        <p>Уважаемый пользователь, здравствуйте!</p>
                        
                        <p>Вы выполняете подтверждение email, введите следующий код для завершения операции:</p>
                        
                        <div class="otp-box">
                            <p style="color: #718096; margin-bottom: 10px;">Ваш код подтверждения:</p>
                            <div class="otp-code">{otp_code}</div>
                            <p class="warning">⚠️ Этот код истечет через 10 минут</p>
                        </div>
                        
                        <div class="instructions">
                            <p><strong>Безопасность:</strong></p>
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                <li>Введите этот код на странице подтверждения</li>
                                <li>Не сообщайте код никому другому</li>
                                <li>Если это не ваше действие, проигнорируйте это письмо</li>
                            </ul>
                        </div>
                        
                        <p>Если вы не запрашивали этот код, проигнорируйте это письмо.</p>
                        
                        <p style="margin-top: 30px;">
                            Приятного использования!<br>
                            Команда {app_name}
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 {app_name}. Все права защищены.</p>
                        <p>Это автоматическое письмо, не отвечайте на него.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Использование реальной функции отправки email
            logger.info(f"📤 Подготовка к отправке OTP через Gmail на: {email}")
            success = await send_email(
                email_to=email,
                subject=subject,
                html_content=html_content
            )
            
            if success:
                # Сохранение OTP в базу данных
                try:
                    # Очистка старых записей OTP
                    old_otps = db.query(OTP).filter(
                        OTP.email == email,
                        OTP.expires_at < datetime.now()
                    ).all()
                    
                    for old_otp in old_otps:
                        db.delete(old_otp)
                    
                    # Создание новой записи OTP
                    otp_record = OTP(
                        email=email,
                        otp_code=otp_code,
                        expires_at=datetime.now() + timedelta(minutes=10)
                    )
                    db.add(otp_record)
                    db.commit()
                    
                    logger.info(f"✅ OTP сохранен в базу данных: {email}")
                    
                except Exception as db_error:
                    logger.error(f"❌ Ошибка сохранения OTP в базу данных: {db_error}")
                    db.rollback()
                
                logger.info(f"✅ Письмо с OTP успешно отправлено: {email}")
                logger.info(f"📧 Код подтверждения: {otp_code} (истечет через 10 минут)")
            else:
                logger.error(f"❌ Ошибка отправки письма с OTP: {email}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке письма с OTP: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def verify_otp(email: str, otp_code: str, db: Session) -> bool:
        """Верификация OTP кода"""
        try:
            # Поиск неиспользованной и неистекшей записи OTP
            otp_record = db.query(OTP).filter(
                OTP.email == email,
                OTP.otp_code == otp_code,
                OTP.is_used == False,
                OTP.expires_at > datetime.now()
            ).first()
            
            if not otp_record:
                logger.warning(f"Ошибка верификации OTP: {email} - неверный или истекший код")
                return False
            
            # Отметка как использованного
            otp_record.is_used = True
            #otp_record.used_at = datetime.now()
            db.commit()
            
            logger.info(f"✅ OTP успешно верифицирован: {email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при верификации OTP: {e}")
            db.rollback()
            return False


# Функции для совместимости
def generate_otp(length: int = 6) -> str:
    return OTPService.generate_otp(length)

async def send_otp_email(email: str, otp_code: str) -> bool:
    """Отправляет письмо с OTP (функция для совместимости)"""
    try:
        from backend.app.core.config import settings
        app_name = getattr(settings, 'APP_NAME', 'FastAPI E-commerce платформа')
        subject = f"{app_name} - Код подтверждения {otp_code}"
        
        html_content = f"""
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #4CAF50;">Код подтверждения email</h2>
            <p>Ваш код подтверждения:</p>
            <div style="font-size: 32px; font-weight: bold; color: #4CAF50; margin: 20px 0; text-align: center;">
                {otp_code}
            </div>
            <p>Код истечет через 10 минут, используйте его как можно скорее.</p>
        </div>
        """
        
        return await send_email(
            email_to=email,
            subject=subject,
            html_content=html_content
        )
    except Exception as e:
        logger.error(f"Ошибка отправки письма с OTP: {e}")
        return False