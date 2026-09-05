.PHONY up down restart build chat

up: 
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart webhook

build:
	docker compose build webhook
	docker compose build chat

chat:
	docker compose run --rm -it chat