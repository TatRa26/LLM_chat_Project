import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from typing import List, Dict
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="langchain")

load_dotenv()


class LlamaService:
    def __init__(self):
        self.client = ChatOpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
            model=os.getenv("MODEL"),
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
        self.memory_file = "chat_history.json"  # Файл для хранения истории

        # Загружаем историю из файла при старте
        self._load_history_from_file()

    def _load_history_from_file(self):
        """Загружает историю из файла JSON"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    for msg in history:
                        if msg["role"] == "user":
                            self.memory.add_user_message(msg["content"])
                        elif msg["role"] == "assistant":
                            self.memory.add_ai_message(msg["content"])
        except Exception as e:
            print(f"Ошибка при загрузке истории: {str(e)}")

    def _save_history_to_file(self):
        """Сохраняет текущую историю в файл JSON"""
        try:
            history = []
            for msg in self.memory.messages:
                if isinstance(msg, HumanMessage):
                    history.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    history.append({"role": "assistant", "content": msg.content})
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
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

            # Сохраняем историю в файл
            self._save_history_to_file()

            return response.content.strip()

        except Exception as e:
            return f"Ошибка при обращении к API: {str(e)}"

    def clear_memory(self):
        """Очищает память и файл истории"""
        self.memory.clear()
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)
