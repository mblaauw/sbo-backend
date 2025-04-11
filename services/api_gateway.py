# api_gateway/main.py
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any, Optional
import httpx
import os
import logging
import time
from datetime import datetime

from services.auth import get_current_user, oauth2_scheme

app = FastAPI(
    title="Skills Based Organization - API Gateway",
    description="Gateway for SBO microservices",
    version="0.1.0",
    #docs_url=None  # We'll customize the docs page
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs from environment variables
SKILLS_SERVICE_URL = os.getenv("SKILLS_SERVICE_URL", "http://localhost:8801")
MATCHING_SERVICE_URL = os.getenv("MATCHING_SERVICE_URL", "http://localhost:8802")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8803")
ASSESSMENT_SERVICE_URL = os.getenv("ASSESSMENT_SERVICE_URL", "http://localhost:8804")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8805")

# Custom OpenAPI docs route
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - API Documentation",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
    )

# Middleware for request logging and timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logging.info(f"Request to {request.url.path} processed in {process_time:.4f} seconds")
    return response

# Error handler for all exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    # Check all service health
    services = {
        "api_gateway": "healthy",
        "skills_service": "unknown",
        "matching_service": "unknown",
        "user_service": "unknown",
        "assessment_service": "unknown",
        "llm_service": "unknown"
    }
    
    async with httpx.AsyncClient() as client:
        # Check Skills Service
        try:
            response = await client.get(f"{SKILLS_SERVICE_URL}/health", timeout=2.0)
            services["skills_service"] = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception as e:
            services["skills_service"] = f"unhealthy: {str(e)}"
        
        # Check Matching Service
        try:
            response = await client.get(f"{MATCHING_SERVICE_URL}/health", timeout=2.0)
            services["matching_service"] = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception as e:
            services["matching_service"] = f"unhealthy: {str(e)}"
        
        # Add checks for other services...
    
    overall_health = "healthy" if all(v == "healthy" for v in services.values()) else "degraded"
    
    return {
        "status": overall_health,
        "timestamp": datetime.now().isoformat(),
        "services": services
    }

# Endpoints proxied to Skills Service
@app.get("/skills/categories")
async def get_skill_categories(token: str = Depends(oauth2_scheme)):
    user = get_current_user(token)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{SKILLS_SERVICE_URL}/skills/categories",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Skills service unavailable: {str(e)}")

@app.get("/skills/category/{category_id}")
async def get_skills_by_category(category_id: int, token: str = Depends(oauth2_scheme)):
    user = get_current_user(token)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{SKILLS_SERVICE_URL}/skills/category/{category_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Skills service unavailable: {str(e)}")

# Endpoints proxied to Matching Service
@app.get("/roles")
async def get_all_roles(
    department: str = None,
    skip: int = 0,
    limit: int = 100,
    token: str = Depends(oauth2_scheme)
):
    user = get_current_user(token)
    params = {}
    if department:
        params["department"] = department
    params["skip"] = skip
    params["limit"] = limit
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{MATCHING_SERVICE_URL}/roles",
                params=params,
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Matching service unavailable: {str(e)}")

@app.post("/match/candidate-role")
async def match_candidate_to_role(match_request: Dict[str, Any], token: str = Depends(oauth2_scheme)):
    user = get_current_user(token)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{MATCHING_SERVICE_URL}/match/candidate-role",
                json=match_request,
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Matching service unavailable: {str(e)}")

# Endpoints proxied to LLM Service
@app.post("/extract-skills")
async def extract_skills_from_text(text_data: Dict[str, str], token: str = Depends(oauth2_scheme)):
    user = get_current_user(token)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{LLM_SERVICE_URL}/extract-skills",
                json=text_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"LLM service unavailable: {str(e)}")

@app.post("/analyze-resume")
async def analyze_resume(resume_data: Dict[str, str], token: str = Depends(oauth2_scheme)):
    user = get_current_user(token)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{LLM_SERVICE_URL}/analyze-resume",
                json=resume_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"LLM service unavailable: {str(e)}")

# Composite endpoints that call multiple services
@app.get("/dashboard/candidate/{candidate_id}")
async def get_candidate_dashboard(candidate_id: int, token: str = Depends(oauth2_scheme)):
    user = get_current_user(token)
    async with httpx.AsyncClient() as client:
        try:
            # Get candidate profile from User Service
            profile_response = await client.get(
                f"{USER_SERVICE_URL}/users/{candidate_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if profile_response.status_code != 200:
                raise HTTPException(status_code=profile_response.status_code, detail=profile_response.text)
            
            profile = profile_response.json()
            
            # Get candidate skills from User Service
            skills_response = await client.get(
                f"{USER_SERVICE_URL}/users/{candidate_id}/skills",
                headers={"Authorization": f"Bearer {token}"}
            )
            if skills_response.status_code != 200:
                raise HTTPException(status_code=skills_response.status_code, detail=skills_response.text)
            
            skills = skills_response.json()
            
            # Get matching roles from Matching Service
            roles_response = await client.get(
                f"{MATCHING_SERVICE_URL}/match/candidate-roles/{candidate_id}",
                params={"min_match_percentage": 60.0, "limit": 5},
                headers={"Authorization": f"Bearer {token}"}
            )
            if roles_response.status_code != 200:
                raise HTTPException(status_code=roles_response.status_code, detail=roles_response.text)
            
            matching_roles = roles_response.json()
            
            # Combine all data
            dashboard_data = {
                "candidate": profile,
                "skills": skills,
                "matching_roles": matching_roles,
                "generated_at": datetime.now().isoformat()
            }
            
            return dashboard_data
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.get("/dashboard/role/{role_id}")
async def get_role_dashboard(role_id: int, token: str = Depends(oauth2_scheme)):
    user = get_current_user(token)
    async with httpx.AsyncClient() as client:
        try:
            # Get role details from Matching Service
            role_response = await client.get(
                f"{MATCHING_SERVICE_URL}/roles/{role_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if role_response.status_code != 200:
                raise HTTPException(status_code=role_response.status_code, detail=role_response.text)
            
            role = role_response.json()
            
            # Get matching candidates from Matching Service
            candidates_response = await client.get(
                f"{MATCHING_SERVICE_URL}/match/role-candidates/{role_id}",
                params={"min_match_percentage": 60.0, "limit": 5},
                headers={"Authorization": f"Bearer {token}"}
            )
            if candidates_response.status_code != 200:
                raise HTTPException(status_code=candidates_response.status_code, detail=candidates_response.text)
            
            matching_candidates = candidates_response.json()
            
            # Combine all data
            dashboard_data = {
                "role": role,
                "matching_candidates": matching_candidates,
                "generated_at": datetime.now().isoformat()
            }
            
            return dashboard_data
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

