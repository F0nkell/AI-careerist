# Используем официальный базовый образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# --- ВАЖНО: Копируем код И файлы миграций ---
COPY src /app/src
COPY alembic /app/alembic
COPY alembic.ini .
# --------------------------------------------

# Указываем, какой порт будет слушать контейнер
EXPOSE 8000

# Команда запуска по умолчанию (переопределяется в docker-compose)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]