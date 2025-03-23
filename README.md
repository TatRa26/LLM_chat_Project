# Чат с LLM

## 1. Настройка переменных окружения:

Создаем файл `.env` в корневой директории проекта:

```bash
MODEL_NAME=название_модели
API_URL=url_модели
API_KEY=ваш_ключ_api
```

### Настройка окружения:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Поднятие сервиса локально

### Запуск Streamlit сервиса:
```bash
make up.local
```

или

```bash
streamlit run main.py
```

## 3. Поднятие сервиса с помощью Docker

### Запуск Streamlit сервиса:
```bash
make build.up
```
По этой команде будет произведени билд образа и поднятие сервиса

или

```bash
docker build -t <image_name> .
docker run -p 8501:8501 --rm --name <container_name> <image_name>
```

Если образ уже билдился ранее, поднять сервис можно по команде:

```bash
make up
```

или

```bash
docker run -p 8501:8501 -v llm_chat_volume:/app/chat_history/ --rm --name <container_name> <image_name>
```

Сервис будет доступен по адресу: http://localhost:8501
