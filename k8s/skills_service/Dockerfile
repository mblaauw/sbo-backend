FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service-specific files
COPY ./services/skills_service /app/skills_service

# Run the service
CMD ["uvicorn", "skills_service.main:app", "--host", "0.0.0.0", "--port", "8100"]