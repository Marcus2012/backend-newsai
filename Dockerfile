FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by some Python packages and Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    wget \
    ca-certificates \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    fonts-liberation \
    libx11-xcb1 \
    libxkbcommon0 \
    libxcb1 \
    libxss1 \
    libxshmfence1 \
    libdrm2 \
    libatspi2.0-0 \
    libpango-1.0-0 \
    libharfbuzz0b \
    fonts-noto-color-emoji \
    # build deps for Python packages
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip/wheel/setuptools then install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and additional OS deps
# Ensure Playwright downloads browsers into an explicit path inside the image
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
# Install only Chromium (saves size) and include OS deps
RUN python -m playwright install --with-deps chromium

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose port (Cloud Run expects 8080 by default)
EXPOSE 8080

# Run the application (Cloud Run compatible configuration)
CMD python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
