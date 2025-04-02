# llm_service/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import os
import httpx
import logging
from datetime import datetime
import json

from . import models

from .database import get_db, engine
from . import models, schemas

# Initialize database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Skills Based Organization - LLM Service",
    description="Service for using LLMs to process skills data",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Skills Service URL
SKILLS_SERVICE_URL = os.getenv("SKILLS_SERVICE_URL", "http://localhost:8801")

# Endpoint to extract skills from text
@app.post("/extract-skills", response_model=List[schemas.ExtractedSkill])
async def extract_skills_from_text(
    text_data: schemas.TextData,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Log the request for later analysis
    background_tasks.add_task(
        log_llm_request, 
        db=db, 
        request_type="extract_skills", 
        input_data=text_data.dict()
    )
    
    try:
        # Call our LLM client to extract skills
        extracted = models.extract_skills_from_text(text_data.text)
        
        # Log the successful response
        background_tasks.add_task(
            log_llm_response, 
            db=db, 
            request_type="extract_skills",
            output_data=extracted
        )
        
        return extracted
    except Exception as e:
        logging.error(f"Error extracting skills: {str(e)}")
        # Log the error
        background_tasks.add_task(
            log_llm_error, 
            db=db, 
            request_type="extract_skills",
            error_msg=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error extracting skills: {str(e)}")

# Endpoint to map free-text skills to taxonomy
@app.post("/map-skills", response_model=List[schemas.MappedSkill])
async def map_skills_to_taxonomy(
    mapping_request: schemas.MappingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Log the request
    background_tasks.add_task(
        log_llm_request, 
        db=db, 
        request_type="map_skills", 
        input_data=mapping_request.dict()
    )
    
    try:
        # Call our LLM client to map skills
        mapped = models.map_skills_to_taxonomy(
            mapping_request.skills, 
            mapping_request.taxonomy
        )
        
        # Log the successful response
        background_tasks.add_task(
            log_llm_response, 
            db=db, 
            request_type="map_skills",
            output_data=mapped
        )
        
        return mapped
    except Exception as e:
        logging.error(f"Error mapping skills: {str(e)}")
        # Log the error
        background_tasks.add_task(
            log_llm_error, 
            db=db, 
            request_type="map_skills",
            error_msg=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error mapping skills: {str(e)}")

# Endpoint to generate assessment questions for a skill
@app.post("/generate-assessment", response_model=schemas.AssessmentQuestions)
async def generate_assessment_questions(
    assessment_request: schemas.AssessmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Log the request
    background_tasks.add_task(
        log_llm_request, 
        db=db, 
        request_type="generate_assessment", 
        input_data=assessment_request.dict()
    )
    
    try:
        # Get skill information from Skills Service if skill_id is provided
        skill_info = None
        if assessment_request.skill_id:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{SKILLS_SERVICE_URL}/skills/{assessment_request.skill_id}")
                    if response.status_code == 200:
                        skill_info = response.json()
            except httpx.RequestError as e:
                logging.warning(f"Could not fetch skill info: {str(e)}")
        
        # Use the skill information or the provided skill name
        skill_name = skill_info["name"] if skill_info else assessment_request.skill_name
        skill_description = skill_info["description"] if skill_info else assessment_request.skill_description
        
        # Call our LLM client to generate assessment questions
        questions = models.generate_assessment_questions(
            skill_name,
            skill_description,
            assessment_request.num_questions,
            assessment_request.difficulty_level
        )
        
        # Log the successful response
        background_tasks.add_task(
            log_llm_response, 
            db=db, 
            request_type="generate_assessment",
            output_data={"questions": questions}
        )
        
        return schemas.AssessmentQuestions(
            skill_id=assessment_request.skill_id,
            skill_name=skill_name,
            questions=questions
        )
    except Exception as e:
        logging.error(f"Error generating assessment: {str(e)}")
        # Log the error
        background_tasks.add_task(
            log_llm_error, 
            db=db, 
            request_type="generate_assessment",
            error_msg=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error generating assessment: {str(e)}")

# Endpoint to analyze a resume and extract skills
@app.post("/analyze-resume", response_model=schemas.ResumeAnalysis)
async def analyze_resume(
    resume_data: schemas.ResumeData,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Log the request
    background_tasks.add_task(
        log_llm_request, 
        db=db, 
        request_type="analyze_resume", 
        input_data={"resume_length": len(resume_data.text)}
    )
    
    try:
        # Call our LLM client to analyze the resume
        analysis = models.analyze_resume(resume_data.text)
        
        # Log the successful response
        background_tasks.add_task(
            log_llm_response, 
            db=db, 
            request_type="analyze_resume",
            output_data={
                "num_skills": len(analysis["skills"]),
                "num_experiences": len(analysis["experiences"])
            }
        )
        
        return schemas.ResumeAnalysis(**analysis)
    except Exception as e:
        logging.error(f"Error analyzing resume: {str(e)}")
        # Log the error
        background_tasks.add_task(
            log_llm_error, 
            db=db, 
            request_type="analyze_resume",
            error_msg=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error analyzing resume: {str(e)}")

# Endpoint to generate a personalized learning path
@app.post("/generate-learning-path", response_model=schemas.LearningPath)
async def generate_learning_path(
    path_request: schemas.LearningPathRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Log the request
    background_tasks.add_task(
        log_llm_request, 
        db=db, 
        request_type="generate_learning_path", 
        input_data=path_request.dict()
    )
    
    try:
        # Call our LLM client to generate a learning path
        learning_path = models.generate_learning_path(
            path_request.user_id,
            path_request.target_skills,
            path_request.current_skills,
            path_request.time_frame
        )
        
        # Log the successful response
        background_tasks.add_task(
            log_llm_response, 
            db=db, 
            request_type="generate_learning_path",
            output_data={"num_steps": len(learning_path["steps"])}
        )
        
        return schemas.LearningPath(**learning_path)
    except Exception as e:
        logging.error(f"Error generating learning path: {str(e)}")
        # Log the error
        background_tasks.add_task(
            log_llm_error, 
            db=db, 
            request_type="generate_learning_path",
            error_msg=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error generating learning path: {str(e)}")

# Utility functions for logging
async def log_llm_request(db: Session, request_type: str, input_data: Dict[str, Any]):
    db_log = models.LLMRequestLog(
        request_type=request_type,
        input_data=json.dumps(input_data),
        timestamp=datetime.now()
    )
    db.add(db_log)
    db.commit()

async def log_llm_response(db: Session, request_type: str, output_data: Dict[str, Any]):
    db_log = models.LLMResponseLog(
        request_type=request_type,
        output_data=json.dumps(output_data),
        timestamp=datetime.now()
    )
    db.add(db_log)
    db.commit()

async def log_llm_error(db: Session, request_type: str, error_msg: str):
    db_log = models.LLMErrorLog(
        request_type=request_type,
        error_message=error_msg,
        timestamp=datetime.now()
    )
    db.add(db_log)
    db.commit()

