# Этап сборки
FROM python:3.11-slim-buster as builder

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование только requirements.txt для лучшего кэширования
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Финальный этап
FROM python:3.11-slim-buster

WORKDIR /app

# Копирование виртуального окружения из этапа сборки
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование остальных файлов проекта
COPY . .

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]