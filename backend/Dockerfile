FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright and general tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install uv

# Install Playwright browsers
RUN playwright install --with-deps chromium

COPY backend/ backend/

ENV PYTHONPATH=/app

CMD ["python3", "backend/src/server.py"]
