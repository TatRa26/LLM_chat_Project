import os
import sqlite3
import warnings

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_openai import ChatOpenAI

from configs import config

warnings.filterwarnings("ignore", category=UserWarning, module="langchain")

class LlamaService:
    def __init__(self, user_id: int = None):
        self.client = ChatOpenAI(
            api_key=config.api_key,
            base_url=config.api_url,
            model=config.model_name,
            temperature=0.1,
            max_tokens=256,
            top_p=0.95
        )

        self.system_prompt = SystemMessage(
            content="Ты - полезный ассистент, который всегда отвечает на русском языке. "
                    "Твои ответы должны быть информативными, но краткими и по существу."
        )

        self.memory: BaseChatMessageHistory = ChatMessageHistory()
        self.db_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_history.db")
        self.load_history = True
        self.user_id = user_id

        self._init_db()
        if self.user_id is None:
            self.user_id = self._get_or_create_user("default_user")
        self._load_history_from_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при инициализации базы данных: {str(e)}")

    def _get_or_create_user(self, username: str) -> int:
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            if result:
                user_id = result[0]
            else:
                cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
                conn.commit()
                cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
                user_id = cursor.fetchone()[0]
            conn.close()
            return user_id
        except Exception as e:
            print(f"Ошибка при получении/создании пользователя: {str(e)}")
            return None

    def _load_history_from_db(self):
        if not self.load_history or self.user_id is None:
            return
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM chat_history WHERE user_id = ? ORDER BY id", (self.user_id,))
            history = cursor.fetchall()
            for role, content in history:
                if role == "user":
                    self.memory.add_user_message(content)
                elif role == "assistant":
                    self.memory.add_ai_message(content)
            conn.close()
        except Exception as e:
            print(f"Ошибка при загрузке истории: {str(e)}")

    def _save_history_to_db(self):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chat_history WHERE user_id = ?", (self.user_id,))
            current_count = cursor.fetchone()[0]
            new_messages = self.memory.messages[current_count:]
            for msg in new_messages:
                if isinstance(msg, HumanMessage):
                    cursor.execute(
                        "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
                        (self.user_id, "user", msg.content)
                    )
                elif isinstance(msg, AIMessage):
                    cursor.execute(
                        "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
                        (self.user_id, "assistant", msg.content)
                    )
            cursor.execute("SELECT COUNT(*) FROM chat_history WHERE user_id = ?", (self.user_id,))
            total_count = cursor.fetchone()[0]
            if total_count > 10000:
                cursor.execute(
                    "DELETE FROM chat_history WHERE user_id = ? AND id IN (SELECT id FROM chat_history WHERE user_id = ? ORDER BY id ASC LIMIT ?)",
                    (self.user_id, self.user_id, total_count - 10000)
                )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при сохранении истории: {str(e)}")

    def generate_response(self, prompt: str, history: list[dict[str, str]]) -> str:
        try:
            # Проверяем, что сообщения из history не дублируются в self.memory
            current_memory_contents = [msg.content for msg in self.memory.messages]
            # Добавляем только те сообщения из history, которых еще нет в self.memory
            for msg in history:
                if msg["content"] not in current_memory_contents:
                    if msg["role"] == "user":
                        self.memory.add_user_message(msg["content"])
                    elif msg["role"] == "assistant":
                        self.memory.add_ai_message(msg["content"])
                    current_memory_contents.append(msg["content"])

            # Проверяем, добавлено ли уже текущее сообщение (prompt) через history
            if history and history[-1]["content"] == prompt and history[-1]["role"] == "user":
                # Если prompt уже добавлен через history, не добавляем его снова
                pass
            else:
                # Если prompt еще не добавлен, добавляем его
                if prompt not in current_memory_contents:
                    self.memory.add_user_message(prompt)
                    current_memory_contents.append(prompt)

            messages = [self.system_prompt]
            messages.extend(self.memory.messages)

            response = self.client.invoke(messages)

            # Добавляем ответ ассистента
            self.memory.add_ai_message(response.content)

            self._save_history_to_db()

            return response.content.strip()

        except Exception as e:
            return f"Ошибка при обращении к API: {str(e)}"

    def clear_memory(self):
        self.memory.clear()
        self.load_history = False

    def print_history(self):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chat_history WHERE user_id = ?", (self.user_id,))
            rows = cursor.fetchall()
            if rows:
                print(f"Содержимое таблицы chat_history для user_id {self.user_id}:")
                print("ID | User ID | Role      | Content")
                print("-" * 50)
                for row in rows:
                    print(f"{row[0]:<2} | {row[1]:<7} | {row[2]:<9} | {row[3]}")
            else:
                print(f"История для user_id {self.user_id} пуста.")
            conn.close()
        except sqlite3.Error as e:
            print(f"Ошибка при чтении базы данных: {e}")
