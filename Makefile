.PHONY: dev serve install ui ui-build clean test test-unit test-stress test-primitive full-node-start full-node-stop

# --- Development ---
dev:
	uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload

serve:
	uv run uvicorn app:app --host 0.0.0.0 --port 8000

install:
	uv sync && cd frontend && pnpm install

ui:
	cd frontend && pnpm dev --host 0.0.0.0

# --- Testing (Primitive Mode - No Docker Required) ---
# Use this for fast, everyday testing on machines with <= 8GB RAM
test:
	uv run pytest -v

test-unit:
	uv run pytest tests/test_tools.py tests/test_agent.py tests/test_app.py -v

test-stress:
	uv run pytest tests/test_stress_*.py tests/test_performance.py -v -s

test-primitive:
	uv run pytest tests/test_localnet_integration.py -v -s

# --- Full Node (Docker Required - 4GB+ RAM) ---
# Use this for final production-grade verification on a real local node
full-node-start:
	./scripts/setup_node.sh start

full-node-stop:
	./scripts/setup_node.sh stop

# --- Optimization ---
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete 2>/dev/null; true
