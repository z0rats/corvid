.PHONY: up rebuild up-backend up-frontend rebuild-backend rebuild-frontend

up:
	docker compose up -d

rebuild:
	docker compose up -d --build

up-backend:
	docker compose up -d backend

up-frontend:
	docker compose up -d frontend

rebuild-backend:
	docker compose up -d --build backend

rebuild-frontend:
	docker compose up -d --build frontend
