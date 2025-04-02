# Skills Based Organization (SBO) Application

A microservices-based application for implementing Skills Based Organization (SBO), focusing on matching people's skills to organizational roles.

## Overview

This application provides a comprehensive solution for Skills Based Organization as described in the documentation, focusing on:

1. Skills taxonomy management
2. Skills assessment
3. Skills matching between people and roles
4. Internal mobility based on skills
5. Skills gap analysis and learning path recommendations

## Architecture

The application is built using a microservices architecture deployed on Kubernetes:

- **API Gateway**: Entry point for all client requests
- **Skills Service**: Manages the skills taxonomy and skills-related operations
- **Matching Service**: Performs skills matching between candidates and roles
- **LLM Service**: Uses language models to process skills data
- **Assessment Service**: Manages skills assessments
- **User Service**: Manages user profiles and their skills

## Key Features

- **Skills Taxonomy**: Structured representation of skills with hierarchical relationships
- **Skills Extraction**: AI-powered extraction of skills from text (resumes, job descriptions)
- **Skills Assessment**: Generation of assessment questions to evaluate skills proficiency
- **Skills Matching**: Advanced matching algorithms to find the best fit between people and roles
- **Learning Paths**: Personalized recommendations for skill development

## Implementation Details

### Backend

- **Programming Language**: Python
- **API Framework**: FastAPI
- **Database**: PostgreSQL (configured for SQLAlchemy)
- **AI/LLM Integration**: Integration with language models for skills processing
- **Container Orchestration**: Kubernetes

### Kubernetes Deployment

The application is designed to be deployed on Kubernetes with:

- Deployment configurations for each microservice
- Service definitions for inter-service communication
- ConfigMaps for environment-specific configuration
- Secrets for sensitive information
- Resource limits and requests for efficient resource usage

## Getting Started

### Prerequisites

- Docker
- Kubernetes cluster
- kubectl CLI

### Deployment

1. Build the Docker images for each service:

```bash
docker build -t sbo-api-gateway:latest ./api_gateway
docker build -t sbo-skills-service:latest ./skills_service
docker build -t sbo-matching-service:latest ./matching_service
docker build -t sbo-llm-service:latest ./llm_service
docker build -t sbo-assessment-service:latest ./assessment_service
docker build -t sbo-user-service:latest ./user_service
```

2. Apply the Kubernetes configurations:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/api-gateway.yaml
kubectl apply -f k8s/skills-service.yaml
kubectl apply -f k8s/matching-service.yaml
kubectl apply -f k8s/llm-service.yaml
kubectl apply -f k8s/assessment-service.yaml
kubectl apply -f k8s/user-service.yaml
```

3. Access the API Gateway:

```bash
kubectl port-forward svc/api-gateway 8100:80
```

The API will be available at http://localhost:8100

## API Endpoints

### Skills Service

- `GET /skills/categories`: Get all skill categories
- `GET /skills/category/{category_id}`: Get skills by category
- `GET /skills/{skill_id}`: Get a specific skill
- `POST /skills/extract`: Extract skills from text using LLM
- `POST /skills/map`: Map free-text skills to taxonomy

### Matching Service

- `GET /roles`: Get all job roles
- `GET /roles/{role_id}`: Get a specific job role
- `POST /match/candidate-role`: Match a candidate to a role
- `GET /match/role-candidates/{role_id}`: Find candidates for a role
- `GET /match/candidate-roles/{candidate_id}`: Find roles for a candidate

### LLM Service

- `POST /extract-skills`: Extract skills from text
- `POST /map-skills`: Map skills to taxonomy
- `POST /generate-assessment`: Generate assessment questions
- `POST /analyze-resume`: Analyze a resume
- `POST /generate-learning-path`: Generate a learning path

## Mock Data

The application includes mock data generators for development and testing:

- Skills taxonomy with sample skills
- Job roles with skill requirements
- Assessment questions
- User profiles with skills

## Future Enhancements

1. Frontend dashboard for skills visualization
2. Integration with learning management systems
3. Advanced analytics for organizational skills gaps
4. Automated skills assessment using AI
5. Integration with external skills databases and standards

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request