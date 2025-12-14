FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install uv

# Install Playwright browsers (needed if frontend executes tools directly)
RUN playwright install --with-deps chromium

# Copy both backend and frontend because frontend imports backend modules
COPY backend/ backend/
COPY frontend/ frontend/

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python3", "frontend/src/web_ui.py", "--port", "8000"]
