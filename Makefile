.PHONY: up down run migrate schema data test check fmt lint

up:
	docker compose up -d

down:
	docker compose down

run:
	uv run manage.py runserver

migrate:
	uv run manage.py migrate

schema:
	@test -n "$(app)" -a -n "$(name)" || (echo "usage: make schema app=<app> name=<name>" && exit 1)
	uv run manage.py makemigrations $(app) --name schema_$(name)

data:
	@test -n "$(app)" -a -n "$(name)" || (echo "usage: make data app=<app> name=<name>" && exit 1)
	uv run manage.py makemigrations $(app) --empty --name data_$(name)

test:
	uv run pytest

check:
	uv run ty check
	uv run manage.py makemigrations --check --dry-run

fmt:
	uv run ruff check --fix
	uv run ruff format
	npx prettier --write frontend

lint:
	uv run ruff check
	uv run ruff format --check
	npx prettier --check frontend

dev:
	$(MAKE) -j2 run vite

vite:
	npm run dev
