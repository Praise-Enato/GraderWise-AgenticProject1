# Variables
PYTHON = python
UV = uv
VENV = .venv
VENV_PYTHON = $(VENV)/bin/python
VENV_ACTIVATE = $(VENV)/bin/activate

.PHONY: install run clean venv

# Step 0: Create virtual environment
venv:
	@if [ ! -f "$(VENV)/bin/python" ]; then \
		echo "Creating virtual environment..."; \
		$(UV) venv $(VENV); \
		echo "Virtual environment created at $(VENV)"; \
	else \
		echo "Virtual environment already exists at $(VENV)"; \
	fi

# Step 1: Create venv and install dependencies
install-backend: venv
	@echo "Installing stable dependencies..."
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt
	@echo "Backend installation complete."

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Frontend installation complete."

install: install-backend install-frontend
	@echo "All dependencies installed successfully!"

# Step 2: Start the Server

run-backend:
	$(VENV_PYTHON) -m uvicorn backend.src.main:app --reload --port 8000

run-frontend:
	cd frontend && npm run dev

# Default run command (starts backend)
run: run-backend

# Run both backend and frontend concurrently
dev:
	$(MAKE) -j 2 run-backend run-frontend

# Optional: Cleanup cache
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

# Stop development servers
stop:
	@echo "Stopping servers..."
	-lsof -ti :8000 | xargs kill -9
	-lsof -ti :3000 | xargs kill -9
	@echo "Servers stopped."