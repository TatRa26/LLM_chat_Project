import logging
import warnings

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain_postgres import PGVector
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

from configs import config, system_prompt, classifier_prompt
from models import User, ChatHistory
from database import get_db

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
warnings.filterwarnings("ignore", category=UserWarning, module="langchain")
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
dataset_names = {
    0: 'cyber_info',
    1: 'documents',
    2: 'dogs',
    3: 'domru',
    4: 'hygiene_and_cosmetics',
    5: 'labor_code',
    6: 'michelin',
    7: 'red_mad_robot',
    8: 'SP35',
    9: 'world_class',
    10: None,
}

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
        self.llm_classifier = self.client.with_structured_output(
            schema=None,
            method='json_mode'
        )
        self.system_prompt = SystemMessage(system_prompt)
        self.memory: BaseChatMessageHistory = ChatMessageHistory()
        self.load_history = True
        self.user_id = user_id
        if self.user_id is None:
            self.user_id = self._get_or_create_user("default_user")
        self._load_history_from_db()

    @staticmethod
    def _get_or_create_user(username: str) -> int | None:
        try:
            # Ищем пользователя по имени
            session = next(get_db())
            user = session.query(User).filter_by(username=username).first()
            if user:
                return user.user_id
            # Если пользователя нет, создаем нового
            new_user = User(username=username)
            session.add(new_user)
            session.commit()
            return new_user.user_id

        except Exception as e:
            logger.exception(f"Ошибка при получении/создании пользователя: {str(e)}")
            return None

    def _load_history_from_db(self) -> None:
        if not self.load_history or self.user_id is None:
            return

        try:
            # Загружаем историю сообщений для пользователя
            session = next(get_db())
            messages = (
                session
                .query(ChatHistory)
                .filter_by(user_id=self.user_id)
                .order_by(ChatHistory.id)
                .all()
            )
            for msg in messages:
                if msg.role == "user":
                    self.memory.add_user_message(msg.content)
                elif msg.role == "assistant":
                    self.memory.add_ai_message(msg.content)

        except Exception as e:
            logger.exception(f"Ошибка при загрузке истории: {str(e)}")

    def _save_history_to_db(self) -> None:
        try:
            session = next(get_db())
            # Подсчитываем текущее количество записей в базе для пользователя
            current_count = (
                session
                .query(ChatHistory)
                .filter_by(user_id=self.user_id).
                count()
            )
            new_messages = self.memory.messages[current_count:]
            for msg in new_messages:
                if isinstance(msg, HumanMessage):
                    new_msg = ChatHistory(user_id=self.user_id, role="user", content=msg.content)
                    session.add(new_msg)
                elif isinstance(msg, AIMessage):
                    new_msg = ChatHistory(user_id=self.user_id, role="assistant", content=msg.content)
                    session.add(new_msg)
            session.commit()
            # Ограничиваем количество записей (аналогично текущей логике)
            total_count = session.query(ChatHistory).filter_by(user_id=self.user_id).count()
            if total_count > 10000:
                excess = total_count - 10000
                oldest_messages = session.query(ChatHistory).filter_by(user_id=self.user_id).order_by(ChatHistory.id).limit(excess).all()
                for msg in oldest_messages:
                    session.delete(msg)
                session.commit()

        except Exception as e:
            logger.exception(f"Ошибка при сохранении истории: {str(e)}")

    @staticmethod
    def _get_vector_store(collection_name: str) -> PGVector:
        vector_store = PGVector(
            embeddings=HuggingFaceEmbeddings(model_name=MODEL_NAME),
            collection_name=collection_name,
            connection=config.postgres_url,
            use_jsonb=True,
        )

        return vector_store

    def _get_rag_context(self, query: str,  collection_name: str, k: int = 1):
        vector_store = self._get_vector_store(collection_name)
        docs = vector_store.similarity_search(
            query, k=k,
            filter={"collection_name": {"$eq": collection_name}}
        )
        result = '\n'.join([doc.page_content for doc in docs])

        return result

    def generate_response(self, prompt: str, history: list[dict[str, str]]) -> str:
        try:
            messages = [
                ('system', classifier_prompt),
                ('user', f"User's query: {prompt}"),
            ]
            response = self.llm_classifier.invoke(messages)
            logger.info(f'Response: {response}')
            context = None
            category = response.get('category')
            if isinstance(category, int):
                try:
                    dataset_name = dataset_names[category]
                    logger.info(f'Category: {dataset_name}')
                    if dataset_name is not None:
                        context = self._get_rag_context(
                            prompt,
                            dataset_name,
                            k=3
                        )
                        logger.info(f'Context: {context}')
                except Exception as e:
                    logger.exception(f'Wrong RAG category: {str(e)}')

            if context is not None:
                prompt = prompt + f'\nКонтекст: {context}'
                logger.info(f'Query: {prompt}')
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
            logger.exception(f'Ошибка в generate_response: {str(e)}')
            return 'Извините, что-то пошло не так. Попробуйте снова!'

    def clear_memory(self):
        self.memory.clear()
        self.load_history = False

    def print_history(self):
        try:
            session = next(get_db())
            messages = session.query(ChatHistory).filter_by(user_id=self.user_id).all()
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
