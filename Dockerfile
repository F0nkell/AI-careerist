# Используем официальный базовый образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src /app/src

# Указываем, какой порт будет слушать контейнер
EXPOSE 8000

# Команда запуска будет переопределена в docker-compose.yml для dev-режима.
# Но для продакшена это будет выглядеть так:
# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]