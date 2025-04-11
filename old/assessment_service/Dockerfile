FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service-specific files
COPY ./services/assessment_service /app/assessment_service

# Run the service
CMD ["uvicorn", "assessment_service.main:app", "--host", "0.0.0.0", "--port", "8804"]