import logging

import torch
import streamlit as st

from database import get_db
from models import User
from src import LlamaService
import json

torch.classes.__path__ = []
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Инициализация состояния сессии
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "change_user" not in st.session_state:
    st.session_state.change_user = False
if "feedback" not in st.session_state:
        st.session_state.feedback = {}

# Инициализация LlamaService
llama = LlamaService(st.session_state.user_id)


# Функция для получения имени пользователя по user_id
def get_username_by_id(user_id: int) -> str | None:
    try:
        session = next(get_db())
        user = session.query(User).filter_by(user_id=user_id).first()
        return user.username if user else None

    except Exception as e:
        logger.exception(f"Ошибка при получении имени пользователя: {str(e)}")
        return None


# Проверяем, соответствует ли username в session_state реальному имени в базе данных
if st.session_state.user_id:
    db_username = get_username_by_id(st.session_state.user_id)
    if db_username and db_username != st.session_state.username:
        st.session_state.username = db_username

st.title("💬 Чат с LLM")

# Основной интерфейс чата (показываем только если пользователь авторизовался)
if st.session_state.user_id is not None and not st.session_state.change_user:
    # Подзаголовок с именем пользователя (только для авторизованных)
    st.subheader(f"Пользователь: {st.session_state.username}")

    # Кнопки управления
    col1, col2, col3, col4  = st.columns(4)
    with col1:
        if st.button("🗑️ Очистить"):
            st.session_state.messages = []
            llama.clear_memory()
            st.rerun()
    with col2:
        if st.button("👤 Сменить пользователя"):
            st.session_state.change_user = True
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
    with col3:
        if st.button("🔄 Сбросить сессию"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.session_state.change_user = True
            st.rerun()
    with col4:
        if st.button("📥 Экспортировать чат"):
            chat_export = []
            for i, message in enumerate(st.session_state.messages):
                entry = {
                    "role": message["role"],
                    "content": message["content"],
                    "feedback": st.session_state.feedback.get(i, "")
                }
                chat_export.append(entry)
            chat_json = json.dumps(chat_export, ensure_ascii=False, indent=2)
            st.download_button(
                label="Скачать чат (JSON)",
                data=chat_json,
                file_name="chat_history.json",
                mime="application/json"
            )

    # История сообщений
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
        # Обратная связь по последнему ответу
    if st.session_state.messages:
        last_index = len(st.session_state.messages) - 1
        last_message = st.session_state.messages[last_index]
        if last_message["role"] == "assistant":
            st.markdown("### 🤖 Оцените последний ответ:")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 Полезный", key="feedback_good"):
                    st.session_state.feedback[last_index] = "Полезный"
            with col2:
                if st.button("👎 Неполезный", key="feedback_bad"):
                    st.session_state.feedback[last_index] = "Неполезный"

            feedback_val = st.session_state.feedback.get(last_index)
            if feedback_val:
                st.success(f"Вы оценили ответ как: {feedback_val}")

            # Пояснение к ответу
            if st.button("💡 Пояснение к ответу"):
                explanation = llama.explain_response(last_message["content"], last_message["content"])
                st.write("Пояснение:", explanation)

            # Аналитика по сессии
            if st.button("📊 Аналитика по сессии"):
                analytics = llama.generate_session_analytics()
                st.write("Аналитика по сессии:", analytics)

    # Поле ввода сообщения
    if prompt := st.chat_input("Введите ваше сообщение"):
        # Добавляем сообщение пользователя в историю для отображения
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Печатает..."):
                response = llama.generate_response(
                    prompt,
                    st.session_state.messages,
                    st.session_state.username
                )
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# Форма ввода имени пользователя (если не авторизован)
else:
    st.write("Пожалуйста, введите ваше имя пользователя:")
    username = st.text_input("Имя пользователя")
    if st.button("Подтвердить имя"):
        if username:
            st.session_state.user_id = llama._get_or_create_user(username)
            st.session_state.username = username
            st.session_state.change_user = False
            st.rerun()

# Кастомные стили
st.markdown("""
    <style>
    .stTextArea textarea {
        border: 2px solid #007bff;
        border-radius: 5px;
        padding: 10px;
    }
    .stButton button {
        background-color: #007bff;
        color: white;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)
