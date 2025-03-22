import sqlite3
import os

db_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_history.db")

try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Проверяем структуру таблиц
    print("Структура базы данных:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        print(f"\nТаблица: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  Столбец: {col[1]} ({col[2]})")

    # Выводим список пользователей
    print("\nСписок пользователей:")
    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()
    if users:
        print("User ID | Username")
        print("-" * 20)
        for user in users:
            print(f"{user[0]:<7} | {user[1]}")
    else:
        print("Пользователи не найдены.")

    # Выводим историю для каждого пользователя
    if users:
        for user_id, username in users:
            print(f"\nИстория для пользователя {username} (user_id: {user_id}):")
            cursor.execute("SELECT * FROM chat_history WHERE user_id = ?", (user_id,))
            rows = cursor.fetchall()
            if rows:
                print("ID | User ID | Role      | Content")
                print("-" * 50)
                for row in rows:
                    print(f"{row[0]:<2} | {row[1]:<7} | {row[2]:<9} | {row[3]}")
            else:
                print("История пуста.")
except sqlite3.Error as e:
    print(f"Ошибка при работе с базой данных: {e}")
finally:
    if conn:
        conn.close()