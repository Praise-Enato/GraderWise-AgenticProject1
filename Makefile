# Variables
UV = uv
VENV = .venv
VENV_PYTHON = $(VENV)/bin/python
# Pinned because torch==2.4.0+cpu only ships wheels up to Python 3.12.
PY = 3.11

.PHONY: env venv install install-backend install-frontend install-dev \
        run run-backend run-frontend dev test clean commit stop

# --- Env scaffolding (optional helper; never overwrites an existing .env) ---
env:
	@if [ ! -f .env ]; then \
		printf 'DEEPSEEK_API_KEY=\nGROQ_API_KEY=\n' > .env; \
		echo "Created .env — fill in DEEPSEEK_API_KEY (required)."; \
	else \
		echo ".env already exists; leaving it untouched."; \
	fi

# --- Install ---
venv:
	@if [ ! -x "$(VENV_PYTHON)" ]; then \
		echo "Creating virtual environment with uv (Python $(PY))..."; \
		$(UV) venv --python $(PY) $(VENV); \
	else \
		echo "Virtual environment already exists at $(VENV)"; \
	fi

# uv installs straight into the venv — no separate pip bootstrap needed.
install-backend: venv
	@echo "Installing backend dependencies with uv..."
	$(UV) pip install --python $(VENV_PYTHON) --index-strategy unsafe-best-match -r requirements.txt
	@echo "Backend installation complete."

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Frontend installation complete."

# Light test-only deps (pytest + pydantic); no torch/langgraph needed.
install-dev: venv
	@echo "Installing dev/test dependencies with uv..."
	$(UV) pip install --python $(VENV_PYTHON) -r requirements-dev.txt
	@echo "Dev dependencies installed."

install: install-backend install-frontend
	@echo "All dependencies installed successfully!"

# --- Run ---
run-backend:
	$(VENV_PYTHON) -m uvicorn backend.src.main:app --reload --port 8000

run-frontend:
	cd frontend && npm run dev

# Default run command (starts backend)
run: run-backend

# Run both backend and frontend concurrently
dev:
	$(MAKE) -j 2 run-backend run-frontend

# --- Test ---
# Runs the backend unit suite (config in pytest.ini). Requires `make install-dev`.
test:
	$(VENV_PYTHON) -m pytest

# --- Utilities ---
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Git commit helper
commit:
	@if [ -z "$(msg)" ]; then \
		echo "Error: Please provide a commit message. Usage: make commit msg=\"your message\""; \
		exit 1; \
	fi
	git add .
	git commit -m "$(msg)"

# Stop development servers (fuser is always present on Ubuntu and
# handles the "no process on port" case cleanly)
stop:
	@echo "Stopping servers on :8000 and :3000..."
	-fuser -k 8000/tcp 2>/dev/null
	-fuser -k 3000/tcp 2>/dev/null
	@echo "Servers stopped."
