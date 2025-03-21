# Чат с LLM

## Настройка переменных окружения

Создаем файл `.env` в корневой директории проекта:

```bash
MODEL_NAME=название_модели
API_URL=url_модели
API_KEY=ваш_ключ_api
```

## Настройка окружения

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```


## Запуск Streamlit сервиса

Сервис будет доступен по адресу: http://localhost:8501

```bash
streamlit run main.py
```
