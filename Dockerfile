FROM python:3.11-slim

WORKDIR /app
# Install system dependencies required for Weasyprint and Playwright
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# playwright browsers
RUN playwright install chromium
RUN playwright install-deps

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
