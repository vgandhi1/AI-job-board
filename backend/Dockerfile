FROM python:3.11-slim

WORKDIR /app

# System deps: postgres client + everything Playwright's bundled Chromium
# needs at runtime (covers Debian 12 / bookworm package names).
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    wget \
    gnupg \
    ca-certificates \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libgtk-3-0 \
    libgdk-pixbuf-2.0-0 \
    libxss1 \
    libxshmfence1 \
    libglib2.0-0 \
    libpng16-16 \
  && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright browser binaries (Chromium) - needed by the ingestion scrapers.
RUN python -m playwright install chromium

# App code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
