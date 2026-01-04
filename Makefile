# Variables
PYTHON = python
UV = uv
VENV = .venv
VENV_PYTHON = $(VENV)\Scripts\python
VENV_ACTIVATE = $(VENV)\Scripts\activate

.PHONY: install run clean venv

# Step 0: Create virtual environment
venv:
	@if not exist "$(VENV)\Scripts\python.exe" ( \
		echo Creating virtual environment... && \
		$(UV) venv $(VENV) && \
		echo Virtual environment created at $(VENV) \
	) else ( \
		echo Virtual environment already exists at $(VENV) \
	)

# Step 1: Create venv and install dependencies
install-backend: venv
	@echo "Cleaning up unstable dependencies..."
	-$(UV) pip uninstall opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation opentelemetry-semantic-conventions chromadb
	@echo "Installing stable dependencies..."
	$(UV) pip install --upgrade pip
	$(UV) pip install -r requirements.txt
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

# Optional: Cleanup cache
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Git commit helper
commit:
	@if "$(msg)"=="" ( \
		echo Error: Please provide a commit message. Usage: make commit msg="your message" && \
		exit 1 \
	)
	git add .
	git commit -m "$(msg)"