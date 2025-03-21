import json
import sqlite3
import os

# Путь к JSON-файлу и базе данных (относительно папки scripts/)
json_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_history.json")
db_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_history.db")

# Инициализация базы данных
conn = sqlite3.connect(db_file)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        content TEXT NOT NULL
    )
""")

# Чтение данных из JSON
if os.path.exists(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        history = json.load(f)
        for msg in history:
            cursor.execute(
                "INSERT INTO chat_history (role, content) VALUES (?, ?)",
                (msg["role"], msg["content"])
            )

# Сохранение изменений
conn.commit()
conn.close()
print("Миграция завершена!")