.PHONY: build up down logs shell test run-host push

build:
	docker compose build

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f bot

shell:
	docker compose exec bot bash

test:
	docker run --rm --env-file .env erik-liminal-calendar-bot python -c "import asyncio, os; from telegram import Bot; print(asyncio.run(Bot(os.environ['ERIK_BOT_TOKEN']).get_me()).username)"

run-host:
	python bot.py

push:
	git push origin master
