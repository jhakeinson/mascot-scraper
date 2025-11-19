# Dockerfile
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

# Install uv
RUN pip install --no-cache-dir uv

# Set workdir
WORKDIR /app

# Copy project
COPY pyproject.toml uv.lock* README.md ./
COPY src ./src

# Install deps with uv
RUN uv sync --frozen --no-cache

# Run scraper
CMD ["uv", "run", "mascot-scraper"]
