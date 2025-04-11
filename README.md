# Skills Based Organization (SBO) Application

A microservices-based application for implementing Skills Based Organization (SBO), focusing on matching people's skills to organizational roles.

## Overview

This application provides a comprehensive solution for Skills Based Organization, enabling:

1. Skills taxonomy management
2. Skills assessment and verification
3. Skills matching between people and roles
4. Internal mobility based on skills
5. Skills gap analysis and learning path recommendations

## Architecture

The application is built using a microservices architecture:

- **API Gateway**: Entry point for all client requests, handles authentication and request routing
- **Skills Service**: Manages the skills taxonomy and skills-related operations
- **Matching Service**: Performs skills matching between candidates and roles
- **User Service**: Manages user profiles and their skills
- **Assessment Service**: Manages skills assessments and results
- **LLM Service**: Uses language models to process skills data

## System Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          Kubernetes Cluster                                │
│                                                                           │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │
│  │  API        │   │  Skills     │   │  Matching   │   │ Assessment  │    │
│  │  Gateway    │   │  Service    │   │  Service    │   │ Service     │    │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘    │
│         │                │                 │                │              │
│         └────────────────┼─────────────────┼────────────────┘              │
│                          │                 │                               │
│                          ▼                 ▼                               │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │
│  │  LLM        │   │  User       │   │  Analytics  │   │ Dashboard   │    │
│  │  Service    │   │  Service    │   │  Service    │   │ Service     │    │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘    │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                       Shared Databases                              │  │
│  │                                                                     │  │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌──────────┐ │  │
│  │  │  Skills     │   │  User       │   │  Job Role   │   │ Assessment│ │  │
│  │  │  Database   │   │  Database   │   │  Database   │   │ Database  │ │  │
│  │  └─────────────┘   └─────────────┘   └─────────────┘   └──────────┘ │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Skills Taxonomy**: Structured representation of skills with hierarchical relationships
- **Skills Extraction**: AI-powered extraction of skills from text (resumes, job descriptions)
- **Skills Assessment**: Generation of assessment questions to evaluate skills proficiency
- **Skills Matching**: Advanced matching algorithms to find the best fit between people and roles
- **Learning Paths**: Personalized recommendations for skill development

## Implementation Details

### Backend

- **Programming Language**: Python 3.8+
- **API Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based with role-based access control
- **AI/LLM Integration**: Integration with language models for skills processing
- **Container Orchestration**: Docker and Kubernetes

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- PostgreSQL (or use the provided Docker container)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/sbo-app.git
cd sbo-app
```

2. Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```
DATABASE_URL=postgresql://sbo_user:sbo_password@localhost:5432/sbo_db
JWT_SECRET_KEY=your-secret-key
LLM_API_KEY=your-llm-api-key
```

### Running with Docker Compose

The easiest way to run the application is with Docker Compose:

```bash
docker-compose up
```

This will start all services and a PostgreSQL database.

### Running for Development

For development, you can run individual services using the development script:

```bash
# Run all services
python run_dev.py

# Run specific services
python run_dev.py api skills user

# Run with debug mode
python run_dev.py --debug
```

### Running Tests

To run the test suite:

```bash
# Run all tests
python run_tests.py 

# Run tests for specific services
python run_tests.py skills matching

# Run with coverage report
python run_tests.py --coverage

# Run with verbose output
python run_tests.py -v
```

## API Documentation

When the services are running, you can access the Swagger UI documentation:

- API Gateway: http://localhost:8800/docs
- Skills Service: http://localhost:8801/docs
- Matching Service: http://localhost:8802/docs
- User Service: http://localhost:8803/docs
- Assessment Service: http://localhost:8804/docs
- LLM Service: http://localhost:8805/docs

## Deployment

### Kubernetes Deployment

1. Build and push the Docker images:

```bash
docker build -t sbo-api-gateway:latest -f Dockerfile.api-gateway .
docker build -t sbo-skills-service:latest -f Dockerfile.skills-service .
# Repeat for other services
```

2. Apply the Kubernetes configurations:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/services/
```

## Project Structure

```
.
├── services/                  # Service implementations
│   ├── __init__.py
│   ├── api_gateway.py         # API Gateway service
│   ├── skills_service.py      # Skills service
│   ├── matching_service.py    # Matching service
│   ├── user_service.py        # User service
│   ├── assessment_service.py  # Assessment service
│   ├── llm_service.py         # LLM service
│   ├── auth_utils.py          # Authentication utilities
│   ├── config.py              # Configuration management
│   ├── database.py            # Database connection handling
│   ├── middleware.py          # Common middleware
│   ├── models.py              # SQLAlchemy models
│   ├── schemas.py             # Pydantic schemas
│   └── llm_models.py          # LLM model implementations
├── tests/                     # Test suite
│   ├── test_skills_service.py
│   ├── test_matching_service.py
│   ├── test_user_service.py
│   ├── test_assessment_service.py
│   ├── test_llm_service.py
│   ├── test_api_gateway.py
│   └── test_integration.py
├── docker-compose.yaml        # Docker Compose configuration
├── k8s/                       # Kubernetes configurations
├── requirements.txt           # Python dependencies
├── run_dev.py                 # Development runner script
├── run_tests.py               # Test runner script
└── README.md                  # This file
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make your changes
4. Run tests to ensure they pass
5. Commit your changes (`git commit -am 'Add new feature'`)
6. Push to the branch (`git push origin feature/new-feature`)
7. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.