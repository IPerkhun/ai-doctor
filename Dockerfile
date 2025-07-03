# Используем официальный образ Python
FROM python:3.10-slim

# Установка зависимостей
RUN apt update && apt install -y build-essential libffi-dev curl

# Установка Poetry или pip зависимостей (мы используем pip)
WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --upgrade pip && pip install -r requirements.txt

# Указываем переменные окружения
ENV PYTHONUNBUFFERED=1

# Открываем порт FastAPI
EXPOSE 8000

# Команда по умолчанию — запуск uvicorn + телеграм-бота
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & python telegram/bot.py"]
