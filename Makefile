up.local:
	streamlit run main.py

up:
	docker compose up

build:
	 docker compose up --build

rebuild:
	docker compose down
	docker compose up --build
