import logging

import streamlit as st

from database import get_db
from models import User
from src import LlamaService
from router import DatasetRouter

logger = logging.getLogger(__name__)

# Инициализация состояния сессии
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "change_user" not in st.session_state:
    st.session_state.change_user = False
if "router" not in st.session_state:
    st.session_state.router = DatasetRouter()

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
    col1, col2, col3 = st.columns(3)
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

    # История сообщений
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Поле ввода сообщения
    if prompt := st.chat_input("Введите ваше сообщение"):
        # Добавляем сообщение пользователя в историю для отображения
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Печатает..."):
                # Определяем подходящий датасет
                dataset_name, similarity = st.session_state.router.router(prompt)
                
                if dataset_name:
                    # Получаем релевантные чанки
                    relevant_chunks = st.session_state.router.get_relevant_chunks(prompt, dataset_name)
                    
                    # Формируем контекст из чанков
                    context = "\n".join([chunk["chunk"] for chunk in relevant_chunks])
                    
                    # Добавляем информацию о датасете в промпт
                    enhanced_prompt = f"Контекст из датасета {dataset_name}:\n{context}\n\nВопрос пользователя: {prompt}"
                    
                    # Генерируем ответ с учетом контекста
                    response = llama.generate_response(enhanced_prompt, st.session_state.messages)
                else:
                    # Если не удалось определить датасет, используем обычный промпт
                    response = llama.generate_response(prompt, st.session_state.messages)
                
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