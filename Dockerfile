FROM python:3.11-slim

WORKDIR /app

# Копирование зависимых файлов
COPY requirements.txt .

# Зависимость от установки
RUN pip install --no-cache-dir -r requirements.txt

# Копировать код приложения
COPY . .

# Открытый порт
EXPOSE 8000

# Запустить команду
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
