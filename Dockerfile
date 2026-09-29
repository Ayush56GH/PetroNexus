# PetroNexus Dockerfile - SIH26121
# Oil India Limited Nearby Well Intelligence Platform

FROM python:3.11-slim

WORKDIR /app

# Install system utilities and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy project source code and assets
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY data/ /app/data/
COPY documents/ /app/documents/
COPY scripts/ /app/scripts/
COPY .env /app/.env

# Create upload and reports directory
RUN mkdir -p /app/uploads /app/reports

# Pre-populate database with seed data
RUN python scripts/seed_database.py
RUN python scripts/index_demo_documents.py

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
