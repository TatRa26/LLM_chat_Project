up.local:
	streamlit run main.py

up:
	docker compose up

down:
	docker compose down

build:
	 docker compose up --build

rebuild:
	docker compose down
	docker compose up --build

db:
	docker compose up db