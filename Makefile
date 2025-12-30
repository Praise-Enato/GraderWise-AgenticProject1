# Variables
PYTHON = python
PIP = pip

.PHONY: install run clean

# Step 1: Nuke conflicting libs and install the safe versions from requirements.txt
install:
	@echo "Cleaning up unstable dependencies..."
	$(PIP) uninstall -y opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation opentelemetry-semantic-conventions chromadb || true
	@echo "Installing stable dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Done! Environment is clean."

# Step 2: Start the Server
run:
	uvicorn backend.src.main:app --reload --port 8000

# Optional: Cleanup cache
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +