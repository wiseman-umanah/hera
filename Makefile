.PHONY: dev serve install ui ui-build docker docker-down clean

dev:
	uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload

serve:
	uv run uvicorn app:app --host 0.0.0.0 --port 8000

install:
	uv sync && cd frontend && pnpm install

ui:
	cd frontend && pnpm dev --host 0.0.0.0

ui-build:
	cd frontend && pnpm build

docker:
	docker compose up --build

docker-down:
	docker compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete 2>/dev/null; true
