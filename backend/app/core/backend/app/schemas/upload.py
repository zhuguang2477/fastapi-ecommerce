# backend/app/schemas/upload.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UploadResponse(BaseModel):
    """Ответ на загрузку"""
    filename: str
    url: str
    thumbnail_url: Optional[str] = None
    size: int
    content_type: str
    uploaded_at: datetime

class MultipleUploadResponse(BaseModel):
    """Ответ на загрузку нескольких файлов"""
    files: List[UploadResponse]
    total_size: int
    success_count: int
    failed_count: int = 0
    failed_files: List[str] = []

class ImageUploadRequest(BaseModel):
    """Запрос на загрузку изображения"""
    folder: Optional[str] = Field("products", description="Папка для хранения")
    resize_width: Optional[int] = Field(None, ge=100, le=5000, description="Ширина для изменения размера")
    resize_height: Optional[int] = Field(None, ge=100, le=5000, description="Высота для изменения размера")
    quality: int = Field(85, ge=1, le=100, description="Качество изображения")

class FileUploadConfig(BaseModel):
    """Конфигурация загрузки файлов"""
    max_file_size: int = 10 * 1024 * 1024  # 10 МБ
    allowed_extensions: List[str] = ["jpg", "jpeg", "png", "gif", "webp"]
    allowed_mime_types: List[str] = [
        "image/jpeg", 
        "image/png", 
        "image/gif", 
        "image/webp"
    ]