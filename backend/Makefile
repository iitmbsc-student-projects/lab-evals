# Makefile for Lab Evaluation Application backend

.PHONY: install run up format lint check deploy

install:
	uv sync

# Run dev server
run:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

up:
	docker compose up --build

# Lint and format
format:
	uv run -m ruff format app

lint:
	uv run -m ruff check --fix app

check: format lint

# Build and deploy to Cloud Run via Cloud Build. See deploy/SETUP.md.
deploy:
	cd .. && gcloud builds submit --config=backend/cloudbuild.yaml .
