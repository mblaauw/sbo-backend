FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create package directories
RUN mkdir -p /app/routes /app/utils /app/mock_data

# Initialize package __init__.py files
RUN echo '"""Package containing routes for the SBO application."""' > /app/routes/__init__.py && \
    echo '"""Package containing utilities for the SBO application."""' > /app/utils/__init__.py && \
    echo '"""Package containing mock data for the SBO application."""' > /app/mock_data/__init__.py && \
    echo '"""Skills Based Organization (SBO) Application"""' > /app/__init__.py

# Copy application code
COPY . .

# Expose port
EXPOSE 8800

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8800"]