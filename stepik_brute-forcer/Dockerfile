FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    python3-tk \
    x11-utils \
    fonts-liberation \
    libappindicator3-1 \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание директории для данных
RUN mkdir -p /app/data

# Создание пользователя для безопасности
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Открытие порта для удаленного доступа
EXPOSE 3000

# Команда по умолчанию
CMD ["python", "main.py"]

# Альтернатива: запуск как сервер Playwright
# CMD ["playwright", "run-server", "--port", "3000", "--host", "0.0.0.0"]