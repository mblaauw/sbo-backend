FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service-specific files
COPY ./assesment_service /app/assesment_service

# Run the service
CMD ["uvicorn", "assesment_service.main:app", "--host", "0.0.0.0", "--port", "8000"]