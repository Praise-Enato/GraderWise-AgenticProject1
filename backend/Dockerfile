# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies (build tools for heavy libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Select which requirements file to install. Defaults to the demo set (Business-Plan
# only, no torch/RAG stack — fits 1 GB, no OOM). Override to requirements.txt to
# re-enable the Educator/RAG features.
ARG REQUIREMENTS=requirements-demo.txt

# Copy every requirements file from the build context (project root) so the ARG can
# select any of them; install only the chosen one.
COPY requirements*.txt ./

# Install any needed packages specified in the selected requirements file
RUN pip install --no-cache-dir -r ${REQUIREMENTS}

# Copy the backend source code into the container
COPY backend ./backend

# The BYUMS rubric CSV and judges' guideline live at the repo ROOT, and the
# /bpc-rubric endpoint resolves them relative to WORKDIR (/app). Without copying
# them into the image, /bpc-rubric 404s in the container (the files exist only at
# the repo root on the host, not inside /app). Filenames contain spaces, so use the
# JSON (exec) form of COPY.
COPY ["BYUMS RUBRIC - Sheet1.csv", "Judging_Instructions_BYUMS_Africa_BPC_2026.md", "./"]

# Expose port 8000 for the API
EXPOSE 8000

# Define environment variable if needed (can be overridden by docker-compose)
# ENV NAME World

# Run uvicorn server
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
