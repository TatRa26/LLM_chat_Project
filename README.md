# Чат с LLM

## 1. Настройка переменных окружения

Создайте файл `.env` в корневой директории проекта и добавьте переменные как в указано в файле .env.example

### Настройка окружения

1. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   ```

2. Активируйте виртуальное окружение:
   ```bash
   source venv/bin/activate
   ```

3. Установите необходимые зависимости:
   ```bash
   pip install -r requirements.txt
   ```

## 2. Поднятие сервиса локально

### Запуск Streamlit сервиса

Используйте одну из следующих команд для запуска:

- С помощью `make`:
    ```bash
    make up.local
    ```

- С помощью `streamlit`:
    ```bash
    streamlit run main.py
    ```

## 3. Поднятие сервиса с помощью Docker

### Запуск Streamlit сервиса

- С помощью `make`:
    ```bash
    make up
    ```
- С помощью `docker`:

    ` docker compose up``bash
   
    ```

Сервис будет доступен по адресу: http://localhost:8501

## 4. Остановка сервиса

```bash
docker compose down
```

Это останавливает и удаляет контейнеры, а также сеть. Данные в базе сохраняются.
