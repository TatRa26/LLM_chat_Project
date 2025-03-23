import sqlite3
import os

# Путь к базе данных
db_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_history/chat_history.db")

# Подключение к базе данных
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Создаем таблицу users
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE
    )
""")

# Проверяем, существует ли старая таблица chat_history
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'")
if cursor.fetchone():
    # Создаем временную таблицу для сохранения данных (если они есть)
    cursor.execute("CREATE TABLE IF NOT EXISTS temp_chat_history AS SELECT * FROM chat_history WHERE 0")
    # Переносим данные из старой таблицы (в данном случае база пуста, но оставим для совместимости)
    cursor.execute("INSERT INTO temp_chat_history (role, content) SELECT role, content FROM chat_history")
    # Удаляем старую таблицу
    cursor.execute("DROP TABLE chat_history")

# Создаем новую таблицу chat_history с правильной структурой
cursor.execute("""
    CREATE TABLE chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
""")

# Если в temp_chat_history есть данные, переносим их (в данном случае база пуста)
# Создаем пользователя по умолчанию для старых данных
cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", ("default_user",))
cursor.execute("SELECT user_id FROM users WHERE username = ?", ("default_user",))
default_user_id = cursor.fetchone()[0]

# Переносим данные из временной таблицы
cursor.execute("INSERT INTO chat_history (user_id, role, content) SELECT ?, role, content FROM temp_chat_history", (default_user_id,))
cursor.execute("DROP TABLE IF EXISTS temp_chat_history")

# Сохраняем изменения
conn.commit()
conn.close()
print("Миграция базы данных завершена!")