import os
import sqlite3
from configs.config import load_config  # Импорт Config из configs/config.py
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from typing import List, Dict
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="langchain")

class LlamaService:
    def __init__(self):
        # Загружаем конфигурацию
        config = load_config()

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

        # Используем ChatMessageHistory вместо ConversationBufferMemory
        self.memory: BaseChatMessageHistory = ChatMessageHistory()
        # Путь к файлу базы данных в корневой директории проекта
        self.db_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_history.db")

        # Инициализируем базу данных и загружаем историю
        self._init_db()
        self._load_history_from_db()

    def _init_db(self):
        """Инициализирует базу данных и создает таблицу, если она не существует"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при инициализации базы данных: {str(e)}")

    def _load_history_from_db(self):
        """Загружает историю из базы данных SQLite"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM chat_history ORDER BY id")
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
        """Сохраняет текущую историю в базу данных SQLite"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            # Очищаем таблицу перед сохранением, чтобы синхронизировать с памятью
            cursor.execute("DELETE FROM chat_history")
            for msg in self.memory.messages:
                if isinstance(msg, HumanMessage):
                    cursor.execute(
                        "INSERT INTO chat_history (role, content) VALUES (?, ?)",
                        ("user", msg.content)
                    )
                elif isinstance(msg, AIMessage):
                    cursor.execute(
                        "INSERT INTO chat_history (role, content) VALUES (?, ?)",
                        ("assistant", msg.content)
                    )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при сохранении истории: {str(e)}")

    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> str:
        try:
            # Синхронизируем историю из st.session_state с памятью
            for msg in history:
                if msg["role"] == "user":
                    self.memory.add_user_message(msg["content"])
                elif msg["role"] == "assistant":
                    self.memory.add_ai_message(msg["content"])

            # Формируем сообщения для модели
            messages = [self.system_prompt]
            messages.extend(self.memory.messages)  # Используем .messages вместо load_memory_variables
            messages.append(HumanMessage(content=prompt))

            # Получаем ответ
            response = self.client.invoke(messages)

            # Добавляем новый запрос и ответ в память
            self.memory.add_user_message(prompt)
            self.memory.add_ai_message(response.content)

            # Сохраняем историю в базу данных
            self._save_history_to_db()

            return response.content.strip()

        except Exception as e:
            return f"Ошибка при обращении к API: {str(e)}"

    def clear_memory(self):
        """Очищает память и базу данных"""
        self.memory.clear()
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при очистке базы данных: {str(e)}")
