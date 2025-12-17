# backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from .config import settings
from backend.app.database import get_db
from ..models.user import User

logger = logging.getLogger(__name__)

# Контекст хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Схема OAuth2 - установка стандартного URL для токенов
oauth2_scheme = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Генерация хеша пароля"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена доступа"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Проверка JWT токена"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.error(f"Ошибка проверки токена: {e}")
        return None

def get_token_payload(token: str) -> Optional[dict]:
    """Получение данных из токена"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}  # Не проверять срок действия
        )
        return payload
    except JWTError as e:
        logger.error(f"Ошибка декодирования токена: {e}")
        return None

def get_user_id_from_token(token: str) -> Optional[int]:
    """Получение ID пользователя из токена"""
    payload = get_token_payload(token)
    if payload:
        return payload.get("user_id")
    return None

def get_email_from_token(token: str) -> Optional[str]:
    """Получение email из токена"""
    payload = get_token_payload(token)
    if payload:
        return payload.get("sub")
    return None

# Получение текущего пользователя
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),  # 修改参数名
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if credentials is None:
        raise credentials_exception
    
    # 从 HTTPAuthorizationCredentials 对象中提取 token 字符串
    token = credentials.credentials
    payload = verify_token(token)  # 现在传入的是字符串
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user

# Получение当前活动用户（也需要修改）
def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前活动用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if credentials is None:
        raise credentials_exception
    
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь не активирован")
    
    return user

# Простой алиас для get_current_user (для совместимости со старым кодом)
def get_current_user_simple(token: str = Depends(oauth2_scheme)):
    """Упрощенная версия получения текущего пользователя (возвращает только данные токена)"""
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен аутентификации",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload