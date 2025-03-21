import streamlit as st

from src import LlamaService


# Инициализация состояния сессии
if "messages" not in st.session_state:
    st.session_state.messages = []

# Инициализация сервиса
llama = LlamaService()

# Заголовок и кнопка очистки
col1, col2 = st.columns([4, 1])
with col1:
    st.title("💬 Чат с LLM")
with col2:
    if st.button("🗑️ Очистить"):
        st.session_state.messages = []
        st.rerun()

# Чтобы с новым сообщением не затирались старые сообщения
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Поле ввода сообщения
if prompt := st.chat_input("Введите ваше сообщение"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Ответ от LLM
    with st.chat_message("assistant"):
        with st.spinner("Печатает..."):
            response = llama.generate_response(prompt, st.session_state.messages)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response}) 
