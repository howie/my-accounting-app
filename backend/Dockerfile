FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy all source files first (needed for pip install)
COPY pyproject.toml README.md ./
COPY src ./src

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy remaining files
COPY alembic.ini ./
COPY alembic ./alembic

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
