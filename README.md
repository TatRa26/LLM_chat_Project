Нейрокот, [26.03.2025 14:54]
Ваше руководство по настройке и запуску сервиса с использованием Streamlit и Docker выглядит достаточно хорошо структурированным. Однако, я заметил несколько повторений и некорректности в тексте. Давайте попробуем сделать его более четким и последовательным:

---

# Чат с LLM

## 1. Настройка переменных окружения

Создайте файл `.env` в корневой директории проекта и добавьте следующие переменные:

```
MODEL_NAME=название_модели
API_URL=url_модели
API_KEY=ваш_ключ_api
```

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

1. Постройте Docker образ и поднимите сервис:
   ```bash
   make build.up
   ```

   Или выполните команды вручную:
   ```bash
   docker build -t <image_name> .
   docker run -p 8501:8501 -v llm_chat_volume:/app/chat_history/ --rm --name <container_name> <image_name>
   ```

2. Если образ уже был собран ранее, запустите сервис с помощью:
   ```bash
   make up
   ```

   Или:
   ```bash
   docker run -p 8501:8501 -v llm_chat_volume:/app/chat_history/ --rm --name <container_name> <image_name>
   ```

Сервис будет доступен по адресу: [http://localhost:8501](http://localhost:8501)

## 4. Запуск приложения через Docker Compose

### 4.1. Запуск сервиса

Запустите контейнеры с помощью `docker-compose`:

```bash
docker-compose up --build -d
```

- Флаг `--build` пересобирает образы.
- Флаг `-d` запускает контейнеры в фоновом режиме.

Проверьте, что контейнеры запущены:

```bash
docker-compose ps
```

Ожидаемый вывод:

```
NAME                     IMAGE                  COMMAND                  SERVICE   CREATED          STATUS          PORTS
llm_chat_project-ap

Нейрокот, [26.03.2025 14:54]
p-1   llm_chat_project-app   "streamlit run main.…"   app       5 seconds ago    Up 4 seconds    0.0.0.0:8501->8501/tcp
llm_chat_project-db-1    postgres:15            "docker-entrypoint.s…"   db        5 seconds ago    Up 5 seconds    0.0.0.0:5432->5432/tcp
```

Откройте приложение в браузере: [http://localhost:8501](http://localhost:8501)

### 4.2. Остановка сервиса

Остановите и удалите контейнеры:

```bash
docker-compose down
```

Это останавливает и удаляет контейнеры, а также сеть. Данные в базе сохраняются благодаря тому, что используется volume `postgres_data`.

---

Это обновленное руководство должно помочь вам настроить и запустить сервис более эффективно.