# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY intelx_search_new.py .
COPY database.json .

# Create empty history file if not exists
RUN touch intelx_history.json

# Set environment variables (will be overridden by .env or docker-compose)
ENV PYTHONUNBUFFERED=1

# Run the script
CMD ["python", "intelx_search_new.py"]
