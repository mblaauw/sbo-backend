# Skills Based Organization (SBO) Application Architecture

## Overview
This document outlines the architecture for a Skills Based Organization (SBO) prototype application that implements the solution described in the provided document. The system focuses on mapping individual skills to organizational needs to improve talent acquisition, internal mobility, and retention.

## System Architecture

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

## Microservices

### API Gateway
- Routes requests to appropriate services
- Handles authentication and authorization
- API documentation (Swagger/OpenAPI)

### Skills Service
- Maintains skills taxonomy
- CRUD operations for skills
- Skills categorization and relationships

### Matching Service
- Performs fit-gap analysis between candidates and roles
- Calculates skills match, undermatch, and overmatch
- Recommends training paths to close skill gaps

### Assessment Service
- Manages skills assessments
- Processes assessment results
- Calibrates assessment difficulty

### LLM Service
- Extracts skills from unstructured text (resumes, job descriptions)
- Maps free-text descriptions to structured skills taxonomy
- Generates personalized assessment questions

### User Service
- Manages user profiles
- Tracks user skills and skill levels
- Handles authentication

### Analytics Service
- Provides insights on skills distribution
- Identifies organizational skill gaps
- Forecasts future skill needs

### Dashboard Service
- Visualizes skill matches for candidates
- Shows organizational skill coverage
- Displays individual development paths

## Data Models

### Skills Data Model
- Hierarchical taxonomy of skills
- Relationships between skills
- Skill definitions in "I can..." format

### User Data Model
- Personal information
- Skill portfolio with proficiency levels
- Assessment history

### Job Role Data Model
- Required skills with minimum proficiency
- Role descriptions
- Skill weighting for matching

### Assessment Data Model
- Question bank by skill
- Assessment templates
- Scoring algorithms

## LLM Integration
The LLM service will help:
1. Map unstructured skill descriptions to the standard taxonomy
2. Generate appropriate assessment questions
3. Extract skills from CVs and job descriptions
4. Suggest development paths based on skill gaps

## API Endpoints
The system will expose RESTful APIs for all core functionalities following FastAPI best practices.