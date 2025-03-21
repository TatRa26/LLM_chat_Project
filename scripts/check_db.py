import sqlite3
import os

# Путь к базе данных (относительно папки scripts/)
db_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_history.db")

# Подключение к базе данных
try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Чтение данных из таблицы
    cursor.execute("SELECT * FROM chat_history")
    rows = cursor.fetchall()

    # Вывод данных
    if rows:
        print("Содержимое таблицы chat_history:")
        for row in rows:
            print(f"ID: {row[0]}, Role: {row[1]}, Content: {row[2]}")
    else:
        print("Таблица chat_history пуста.")

except sqlite3.Error as e:
    print(f"Ошибка при работе с базой данных: {e}")

finally:
    # Закрытие соединения
    if conn:
        conn.close()