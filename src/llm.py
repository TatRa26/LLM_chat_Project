import logging
import os
import warnings

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from typing import List, Dict

from configs import config

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=UserWarning, module="langchain")

# Настройка SQLAlchemy
Base = declarative_base()

# Модель для таблицы users
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    messages = relationship("ChatHistory", back_populates="user")

# Модель для таблицы chat_history
class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    user = relationship("User", back_populates="messages")

system_prompt = """
Ты - полезный ассистент, который всегда отвечает на русском языке. \
Твои ответы должны быть информативными, но краткими и по существу.
"""

class LlamaService:
    def __init__(self, user_id: int = None) -> None:
        self.client = ChatOpenAI(
            api_key=config.api_key,
            base_url=config.api_url,
            model=config.model_name,
            temperature=0.1,
            max_tokens=256,
            top_p=0.95
        )

        self.system_prompt = SystemMessage(system_prompt)

        self.memory: BaseChatMessageHistory = ChatMessageHistory()
        self.load_history = True
        self.user_id = user_id

        # Подключение к базе данных через SQLAlchemy
        database_url = os.getenv("DATABASE_URL", "sqlite:///chat_history.db")
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)  # Создаем таблицы, если их нет
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        if self.user_id is None:
            self.user_id = self._get_or_create_user("default_user")
        self._load_history_from_db()

    def _get_or_create_user(self, username: str) -> int | None:
        try:
            # Ищем пользователя по имени
            user = self.session.query(User).filter_by(username=username).first()
            if user:
                return user.user_id
            # Если пользователя нет, создаем нового
            new_user = User(username=username)
            self.session.add(new_user)
            self.session.commit()
            return new_user.user_id
        except Exception as e:
            logger.exception(f"Ошибка при получении/создании пользователя: {str(e)}")
            return None

    def _load_history_from_db(self) -> None:
        if not self.load_history or self.user_id is None:
            return
        try:
            # Загружаем историю сообщений для пользователя
            messages = self.session.query(ChatHistory).filter_by(user_id=self.user_id).order_by(ChatHistory.id).all()
            for msg in messages:
                if msg.role == "user":
                    self.memory.add_user_message(msg.content)
                elif msg.role == "assistant":
                    self.memory.add_ai_message(msg.content)
        except Exception as e:
            logger.exception(f"Ошибка при загрузке истории: {str(e)}")

    def _save_history_to_db(self) -> None:
        try:
            # Подсчитываем текущее количество записей в базе для пользователя
            current_count = self.session.query(ChatHistory).filter_by(user_id=self.user_id).count()
            new_messages = self.memory.messages[current_count:]
            for msg in new_messages:
                if isinstance(msg, HumanMessage):
                    new_msg = ChatHistory(user_id=self.user_id, role="user", content=msg.content)
                    self.session.add(new_msg)
                elif isinstance(msg, AIMessage):
                    new_msg = ChatHistory(user_id=self.user_id, role="assistant", content=msg.content)
                    self.session.add(new_msg)
            # Ограничиваем количество записей (аналогично текущей логике)
            total_count = self.session.query(ChatHistory).filter_by(user_id=self.user_id).count()
            if total_count > 10000:
                excess = total_count - 10000
                oldest_messages = self.session.query(ChatHistory).filter_by(user_id=self.user_id).order_by(ChatHistory.id).limit(excess).all()
                for msg in oldest_messages:
                    self.session.delete(msg)
            self.session.commit()
        except Exception as e:
            logger.exception(f"Ошибка при сохранении истории: {str(e)}")
            self.session.rollback()

    def generate_response(self, prompt: str, history: List[Dict[str, str]]) -> str:
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
            messages = self.session.query(ChatHistory).filter_by(user_id=self.user_id).all()
            if messages:
                print(f"Содержимое таблицы chat_history для user_id {self.user_id}:")
                print("ID | User ID | Role      | Content")
                print("-" * 50)
                for msg in messages:
                    print(f"{msg.id:<2} | {msg.user_id:<7} | {msg.role:<9} | {msg.content}")
            else:
                print(f"История для user_id {self.user_id} пуста.")
        except Exception as e:
            logger.exception(f"Ошибка при чтении базы данных: {e}")

    def __del__(self):
        self.session.close()
