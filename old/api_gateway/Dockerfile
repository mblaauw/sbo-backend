FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service-specific files
COPY ./services/api_gateway /app/api_gateway

# Run the service
CMD ["uvicorn", "api_gateway.main:app", "--host", "0.0.0.0", "--port", "8801"]