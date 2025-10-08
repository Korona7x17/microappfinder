FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# API and worker code will be mounted as volumes

# Run the worker - use rq directly
CMD ["rq", "worker", "--url", "redis://redis:6379/0", "default"]
