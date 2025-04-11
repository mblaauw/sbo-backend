"""
LLM service endpoints for SBO application.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import logging
from database import get_db
from middleware import get_current_user, User
from utils.llm_utils import log_llm_request, log_llm_response, log_llm_error
import schemas
from mock_data import (
    extract_skills_from_text, generate_llm_assessment_questions,
    analyze_resume, generate_learning_path
)

logger = logging.getLogger("sbo.llm_routes")

router = APIRouter(tags=["llm"])

@router.post("/extract-skills", response_model=List[schemas.ExtractedSkill])
async def extract_skills_endpoint(
    text_data: schemas.TextData,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """Extract skills from text using LLM"""
    # Log the LLM request
    background_tasks.add_task(
        log_llm_request,
        request_type="extract_skills",
        input_data={"text_length": len(text_data.text)}
    )

    try:
        # Extract skills from text
        extracted = extract_skills_from_text(text_data.text)

        # Log the successful response
        background_tasks.add_task(
            log_llm_response,
            request_type="extract_skills",
            output_data={"num_skills": len(extracted)}
        )

        return extracted
    except Exception as e:
        logger.error(f"Error extracting skills: {str(e)}")
        # Log the error
        background_tasks.add_task(
            log_llm_error,
            request_type="extract_skills",
            error_msg=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error extracting skills: {str(e)}")

@router.post("/generate-assessment", response_model=schemas.AssessmentQuestions)
async def generate_assessment_endpoint(
    assessment_request: schemas.AssessmentRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate assessment questions for a skill"""
    # Log the LLM request
    background_tasks.add_task(
        log_llm_request,
        request_type="generate_assessment",
        input_data=assessment_request.dict()
    )

    try:
        # Get skill information if skill_id is provided
        skill_name = assessment_request.skill_name
        # skill_description = assessment_request.skill_description

        if assessment_request.skill_id:
            from models import Skill
            skill = db.query(Skill).filter(Skill.id == assessment_request.skill_id).first()
            if skill:
                skill_name = skill.name
                # skill_description = skill.description

        if not skill_name:
            raise HTTPException(status_code=400, detail="Either skill_id or skill_name must be provided")

        # Generate questions
        questions = generate_llm_assessment_questions(
            skill_name,
            assessment_request.num_questions
        )

        # Log the successful response
        background_tasks.add_task(
            log_llm_response,
            request_type="generate_assessment",
            output_data={"num_questions": len(questions["questions"])}
        )

        return schemas.AssessmentQuestions(
            skill_id=assessment_request.skill_id,
            skill_name=skill_name,
            questions=questions["questions"]
        )
    except Exception as e:
        logger.error(f"Error generating assessment: {str(e)}")
        # Log the error
        background_tasks.add_task(
            log_llm_error,
            request_type="generate_assessment",
            error_msg=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error generating assessment: {str(e)}")

@router.post("/analyze-resume", response_model=schemas.ResumeAnalysis)
async def analyze_resume_endpoint(
    resume_data: schemas.ResumeData,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """Analyze a resume and extract skills and experiences"""
    # Log the LLM request
    background_tasks.add_task(
        log_llm_request,
        request_type="analyze_resume",
        input_data={"resume_length": len(resume_data.text)}
    )

    try:
        # Analyze resume
        analysis = analyze_resume(resume_data.text)

        # Log the successful response
        background_tasks.add_task(
            log_llm_response,
            request_type="analyze_resume",
            output_data={
                "num_skills": len(analysis["skills"]),
                "num_experiences": len(analysis["experiences"])
            }
        )

        return schemas.ResumeAnalysis(**analysis)
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}")
        # Log the error
        background_tasks.add_task(
            log_llm_error,
            request_type="analyze_resume",
            error_msg=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error analyzing resume: {str(e)}")

@router.post("/generate-learning-path", response_model=schemas.LearningPath)
async def generate_learning_path_endpoint(
    path_request: schemas.LearningPathRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """Generate a personalized learning path for a user"""
    # Log the LLM request
    background_tasks.add_task(
        log_llm_request,
        request_type="generate_learning_path",
        input_data={"user_id": path_request.user_id}
    )

    try:
        # Generate learning path
        learning_path = generate_learning_path(
            path_request.user_id,
            path_request.target_skills,
            path_request.current_skills,
            path_request.time_frame
        )

        # Log the successful response
        background_tasks.add_task(
            log_llm_response,
            request_type="generate_learning_path",
            output_data={"num_steps": len(learning_path["steps"])}
        )

        return schemas.LearningPath(**learning_path)
    except Exception as e:
        logger.error(f"Error generating learning path: {str(e)}")
        # Log the error
        background_tasks.add_task(
            log_llm_error,
            request_type="generate_learning_path",
            error_msg=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error generating learning path: {str(e)}")
