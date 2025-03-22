import streamlit as st
import sqlite3
from src.llm import LlamaService

# Инициализация состояния сессии
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "change_user" not in st.session_state:
    st.session_state.change_user = False

# Функция для получения имени пользователя по user_id
def get_username_by_id(user_id, db_file):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Ошибка при получении имени пользователя: {str(e)}")
        return None

# Поле для ввода имени пользователя
if st.session_state.user_id is None or st.session_state.change_user:
    st.write("Пожалуйста, введите ваше имя пользователя:")
    username = st.text_input("Имя пользователя", value="", placeholder="Введите имя")
    if st.button("Подтвердить имя"):
        if username:
            temp_llama = LlamaService()
            user_id = temp_llama._get_or_create_user(username)
            st.session_state.user_id = user_id
            st.session_state.username = username
            st.session_state.change_user = False
            st.rerun()
        else:
            st.error("Пожалуйста, введите имя пользователя.")

# Инициализация сервиса с user_id
llama = LlamaService(user_id=st.session_state.user_id)

# Проверяем, соответствует ли username в session_state реальному имени в базе данных
if st.session_state.user_id:
    db_username = get_username_by_id(st.session_state.user_id, llama.db_file)
    if db_username and db_username != st.session_state.username:
        st.session_state.username = db_username

# Заголовок и кнопки
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    st.title(f"💬 Чат с LLM (Пользователь: {st.session_state.username})")
with col2:
    if st.button("🗑️ Очистить"):
        st.session_state.messages = []
        llama.clear_memory()
        st.rerun()
with col3:
    if st.button("👤 Сменить пользователя"):
        st.session_state.change_user = True
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()
with col4:
    if st.button("🔄 Сбросить сессию"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.session_state.change_user = True
        st.rerun()

# Отображение сообщений
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
            # Передаем полную историю
            response = llama.generate_response(prompt, st.session_state.messages)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})