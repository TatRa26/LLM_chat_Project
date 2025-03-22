IMAGE_NAME=llm_chat_image
CONTAINER_NAME=llm_chat
PORT=8501

up.local:
	streamlit run main.py

build:
	 docker build -t $(IMAGE_NAME) .

up:
	docker run -p $(PORT):8501 --rm --name $(CONTAINER_NAME) $(IMAGE_NAME)

build.up: build up