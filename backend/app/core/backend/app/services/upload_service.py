# backend/app/services/upload_service.py
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from fastapi import UploadFile, HTTPException
import imghdr
from PIL import Image
import io

from backend.app.core.config import settings
from backend.app.schemas.upload import UploadResponse, ImageUploadRequest

logger = logging.getLogger(__name__)

class UploadService:
    """Сервис загрузки файлов"""
    
    def __init__(self):
        # Убедимся, что директория загрузки существует
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        
        # Создаем поддиректории
        self.product_images_dir = self.upload_dir / "products"
        self.product_images_dir.mkdir(exist_ok=True)
        
        self.shop_images_dir = self.upload_dir / "shops"
        self.shop_images_dir.mkdir(exist_ok=True)
        
        self.temp_dir = self.upload_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        
        logger.info(f"Директория загрузки инициализирована: {self.upload_dir.absolute()}")
    
    def get_upload_path(self, folder: str = "products", filename: str = None) -> Path:
        """Получить путь для загрузки"""
        if folder == "products":
            base_dir = self.product_images_dir
        elif folder == "shops":
            base_dir = self.shop_images_dir
        else:
            base_dir = self.upload_dir / folder
            base_dir.mkdir(exist_ok=True)
        
        if filename:
            return base_dir / filename
        return base_dir
    
    def validate_image_file(self, file: UploadFile) -> Tuple[bool, str]:
        """Валидация изображения"""
        # Проверка размера файла
        max_size = settings.MAX_UPLOAD_SIZE if hasattr(settings, 'MAX_UPLOAD_SIZE') else 10 * 1024 * 1024
        file.file.seek(0, 2)  # Переместиться в конец файла
        file_size = file.file.tell()
        file.file.seek(0)  # Сбросить указатель файла
        
        if file_size > max_size:
            return False, f"Размер файла превышает лимит ({file_size} > {max_size})"
        
        # Проверка расширения файла
        filename = file.filename.lower()
        allowed_extensions = ["jpg", "jpeg", "png", "gif", "webp"]
        
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            return False, f"Неподдерживаемый тип файла, разрешены: {', '.join(allowed_extensions)}"
        
        # Проверка MIME-типа
        content = file.file.read(512)
        file.file.seek(0)
        
        image_type = imghdr.what(None, content)
        if not image_type:
            return False, "Файл не является корректным изображением"
        
        allowed_types = ["jpeg", "png", "gif", "webp"]
        if image_type not in allowed_types:
            return False, f"Неподдерживаемый тип изображения: {image_type}"
        
        return True, "Валидация пройдена"
    
    async def upload_image(
        self,
        file: UploadFile,
        folder: str = "products",
        config: Optional[ImageUploadRequest] = None
    ) -> UploadResponse:
        """Загрузить одно изображение"""
        try:
            # Валидация файла
            is_valid, message = self.validate_image_file(file)
            if not is_valid:
                raise HTTPException(status_code=400, detail=message)
            
            # Генерация уникального имени файла
            original_filename = Path(file.filename).stem
            extension = Path(file.filename).suffix.lower()
            unique_filename = f"{uuid.uuid4().hex}{extension}"
            
            # Получение пути загрузки
            upload_path = self.get_upload_path(folder, unique_filename)
            
            # Чтение содержимого файла
            file_content = await file.read()
            
            # Сохранение оригинального изображения
            with open(upload_path, "wb") as f:
                f.write(file_content)
            
            # Создание миниатюры
            thumbnail_content = self._create_thumbnail(file_content)
            thumbnail_filename = f"thumb_{unique_filename}"
            thumbnail_path = self.get_upload_path(folder, thumbnail_filename)
            
            with open(thumbnail_path, "wb") as f:
                f.write(thumbnail_content)
            
            thumbnail_url = f"/uploads/{folder}/{thumbnail_filename}"
            
            # Если есть конфигурация для изменения размера изображения
            if config and (config.resize_width or config.resize_height):
                try:
                    processed_content = self._process_image(
                        file_content,
                        resize_width=config.resize_width,
                        resize_height=config.resize_height,
                        quality=config.quality
                    )
                    
                    # Сохранение обработанного изображения
                    processed_filename = f"processed_{unique_filename}"
                    processed_path = self.get_upload_path(folder, processed_filename)
                    
                    with open(processed_path, "wb") as f:
                        f.write(processed_content)
                    
                    # Использование обработанного изображения как основного
                    file_url = f"/uploads/{folder}/{processed_filename}"
                except Exception as e:
                    logger.warning(f"Обработка изображения не удалась, используется оригинал: {e}")
                    file_url = f"/uploads/{folder}/{unique_filename}"
            else:
                file_url = f"/uploads/{folder}/{unique_filename}"
            
            # Получение информации о файле
            file_size = os.path.getsize(upload_path)
            
            logger.info(f"Изображение успешно загружено: {file_url}")
            
            return UploadResponse(
                filename=original_filename + extension,
                url=file_url,
                thumbnail_url=thumbnail_url,
                size=file_size,
                content_type=file.content_type,
                uploaded_at=datetime.utcnow()
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка загрузки изображения: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка загрузки: {str(e)}")
    
    async def upload_multiple_images(
        self,
        files: List[UploadFile],
        folder: str = "products",
        config: Optional[ImageUploadRequest] = None
    ) -> Dict[str, Any]:
        """Загрузить несколько изображений"""
        uploaded_files = []
        failed_files = []
        
        for file in files:
            try:
                result = await self.upload_image(file, folder, config)
                uploaded_files.append(result)
            except Exception as e:
                failed_files.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        total_size = sum(f.size for f in uploaded_files)
        
        return {
            "files": uploaded_files,
            "total_size": total_size,
            "success_count": len(uploaded_files),
            "failed_count": len(failed_files),
            "failed_files": failed_files
        }
    
    def _process_image(
        self,
        image_content: bytes,
        resize_width: Optional[int] = None,
        resize_height: Optional[int] = None,
        quality: int = 85
    ) -> bytes:
        """Обработка изображения (изменение размера, качества)"""
        try:
            image = Image.open(io.BytesIO(image_content))
            
            # Изменение размера с сохранением пропорций
            if resize_width or resize_height:
                original_width, original_height = image.size
                
                if resize_width and resize_height:
                    new_size = (resize_width, resize_height)
                elif resize_width:
                    ratio = resize_width / original_width
                    new_height = int(original_height * ratio)
                    new_size = (resize_width, new_height)
                else:  # resize_height
                    ratio = resize_height / original_height
                    new_width = int(original_width * ratio)
                    new_size = (new_width, resize_height)
                
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Сохранение в формате JPEG (если необходимо)
            output_format = "JPEG" if image.format != "PNG" else "PNG"
            
            output = io.BytesIO()
            image.save(output, format=output_format, quality=quality, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {e}")
            # Если обработка не удалась, возвращаем оригинальное содержимое
            return image_content
    
    def _create_thumbnail(
        self,
        image_content: bytes,
        size: Tuple[int, int] = (200, 200)
    ) -> bytes:
        """Создание миниатюры"""
        try:
            image = Image.open(io.BytesIO(image_content))
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            
            # Сохранение в зависимости от исходного формата
            if image.format == "PNG":
                image.save(output, format="PNG", optimize=True)
            else:
                image.save(output, format="JPEG", quality=80, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Ошибка создания миниатюры: {e}")
            return image_content
    
    def delete_file(self, file_url: str) -> bool:
        """Удаление файла"""
        try:
            # Извлечение пути к файлу из URL
            if file_url.startswith("/uploads/"):
                relative_path = file_url[1:]  # Удаляем начальный слеш
                file_path = Path(relative_path)
                
                # Убедимся, что путь находится внутри директории upload
                if not file_path.is_relative_to(self.upload_dir):
                    raise ValueError("Недопустимый путь к файлу")
                
                # Удаление основного файла
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Файл успешно удален: {file_path}")
                
                # Попытка удалить миниатюру
                thumb_path = file_path.parent / f"thumb_{file_path.name}"
                if thumb_path.exists():
                    thumb_path.unlink()
                
                # Попытка удалить обработанное изображение
                processed_path = file_path.parent / f"processed_{file_path.name}"
                if processed_path.exists():
                    processed_path.unlink()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка удаления файла: {e}")
            return False
    
    def cleanup_temp_files(self, older_than_hours: int = 24):
        """Очистка временных файлов"""
        try:
            cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
            
            for temp_file in self.temp_dir.iterdir():
                if temp_file.is_file() and temp_file.stat().st_mtime < cutoff_time:
                    temp_file.unlink()
                    
            logger.info("Очистка временных файлов завершена")
            
        except Exception as e:
            logger.error(f"Ошибка очистки временных файлов: {e}")