# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies (build tools for heavy libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file from the build context (project root)
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source code into the container
COPY backend ./backend

# Expose port 8000 for the API
EXPOSE 8000

# Define environment variable if needed (can be overridden by docker-compose)
# ENV NAME World

# Run uvicorn server
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
