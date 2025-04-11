"""
Consolidated services module for SBO application.
All microservices are combined into a single module for simplified deployment.
"""

import os
import logging
import httpx
import json
import random
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from contextlib import contextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Security, status, Request
from fastapi.security import SecurityScopes
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from config import get_settings
from database import get_db, init_db, get_db_context
from middleware import setup_middleware, get_current_user, admin_required, User, oauth2_scheme
import schemas
import models
from models import (
    Base, SkillCategory, Skill, User as UserModel, UserSkill, JobRole, 
    RoleSkillRequirement, MatchHistory, Assessment, AssessmentQuestion, 
    AssessmentResult, LLMRequestLog, LLMResponseLog, LLMErrorLog
)

# Import mock_data module but avoid circular imports
# Only import the data loading functions here
from mock_data import (
    get_mock_skills_taxonomy, get_mock_users, get_mock_job_roles, 
    get_mock_assessments
)

logger = logging.getLogger("sbo.services")
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Skills Based Organization API",
    description="Unified API for Skills Based Organization services",
    version=settings.app_version
)

# Set up middleware for error handling, logging, etc.
setup_middleware(app)

####################################
# Utility Functions (for LLM)
####################################
def log_llm_request(db: Session, request_type: str, input_data: Dict[str, Any]):
    """Log an LLM request to the database"""
    try:
        db_log = LLMRequestLog(
            request_type=request_type,
            input_data=json.dumps(input_data),
            timestamp=datetime.now()
        )
        db.add(db_log)
        db.commit()
    except Exception as e:
        logger.error(f"Error logging LLM request: {str(e)}")
        db.rollback()

def log_llm_response(db: Session, request_type: str, output_data: Dict[str, Any]):
    """Log an LLM response to the database"""
    try:
        db_log = LLMResponseLog(
            request_type=request_type,
            output_data=json.dumps(output_data),
            timestamp=datetime.now()
        )
        db.add(db_log)
        db.commit()
    except Exception as e:
        logger.error(f"Error logging LLM response: {str(e)}")
        db.rollback()

def log_llm_error(db: Session, request_type: str, error_msg: str):
    """Log an LLM error to the database"""
    try:
        db_log = LLMErrorLog(
            request_type=request_type,
            error_message=error_msg,
            timestamp=datetime.now()
        )
        db.add(db_log)
        db.commit()
    except Exception as e:
        logger.error(f"Error logging LLM error: {str(e)}")
        db.rollback()

# Forward declaration of these functions to avoid circular imports
# The actual implementations will be imported from mock_data module when needed
def extract_skills_from_text(text: str) -> List[Dict[str, Any]]:
    """Extract skills from unstructured text"""
    # Import here to avoid circular import
    from mock_data import extract_skills_from_text as impl
    return impl(text)

def map_skills_to_taxonomy(skills: List[str], taxonomy: List[str]) -> List[Dict[str, Any]]:
    """Map free-text skills to a standardized skills taxonomy"""
    # Import here to avoid circular import
    from mock_data import map_skills_to_taxonomy as impl
    return impl(skills, taxonomy)

def generate_llm_assessment_questions(skill_name: str, num_questions: int = 3) -> Dict[str, Any]:
    """Generate mock assessment questions as if from an LLM"""
    # Import here to avoid circular import
    from mock_data import generate_llm_assessment_questions as impl
    return impl(skill_name, num_questions)

def analyze_resume(resume_text: str) -> Dict[str, Any]:
    """Mock function to analyze a resume and extract skills and experiences"""
    # Import here to avoid circular import
    from mock_data import analyze_resume as impl
    return impl(resume_text)

def generate_learning_path(
    user_id: int, 
    target_skills: List[Dict[str, Any]], 
    current_skills: List[Dict[str, Any]], 
    time_frame: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a mock personalized learning path"""
    # Import here to avoid circular import
    from mock_data import generate_learning_path as impl
    return impl(user_id, target_skills, current_skills, time_frame)

####################################
# Startup Event
####################################
@app.on_event("startup")
async def startup_event():
    """Initialize database tables and load mock data if needed"""
    init_db()
    
    # Initialize with mock data if tables are empty
    db = next(get_db())
    try:
        init_mock_data_if_needed(db)
    finally:
        db.close()

def init_mock_data_if_needed(db: Session):
    """Initialize database with mock data if tables are empty"""
    # Check if skills table is empty
    if db.query(Skill).count() == 0:
        logger.info("Initializing database with mock skills taxonomy")
        skills_data = get_mock_skills_taxonomy()
        
        # Add skill categories
        for category in skills_data.get("categories", []):
            db_category = SkillCategory(**category)
            db.add(db_category)
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error adding skill categories: {str(e)}")
            db.rollback()
            return
        
        # Add skills
        for skill in skills_data.get("skills", []):
            db_skill = Skill(**skill)
            db.add(db_skill)
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error adding skills: {str(e)}")
            db.rollback()
            return
    
    # Check if users table is empty
    if db.query(UserModel).count() == 0:
        logger.info("Initializing database with mock users")
        users_data = get_mock_users()
        
        for user_data in users_data:
            # Extract skills before creating user
            skills_data = user_data.pop("skills", [])
            
            # Create user
            db_user = UserModel(**user_data)
            db.add(db_user)
            
            try:
                db.flush()  # To get the user ID
            except Exception as e:
                logger.error(f"Error adding user: {str(e)}")
                db.rollback()
                return
            
            # Add skills
            for skill_data in skills_data:
                user_skill = UserSkill(
                    user_id=db_user.id,
                    **skill_data
                )
                db.add(user_skill)
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error adding user skills: {str(e)}")
            db.rollback()
            return
    
    # Check if job roles table is empty
    if db.query(JobRole).count() == 0:
        logger.info("Initializing database with mock job roles")
        roles_data = get_mock_job_roles()
        
        for role_data in roles_data:
            # Extract required skills before creating role
            required_skills = role_data.pop("required_skills", [])
            
            # Create role
            db_role = JobRole(**role_data)
            db.add(db_role)
            
            try:
                db.flush()  # To get the role ID
            except Exception as e:
                logger.error(f"Error adding job role: {str(e)}")
                db.rollback()
                return
            
            # Add required skills
            for skill_req in required_skills:
                db_skill_req = RoleSkillRequirement(
                    role_id=db_role.id,
                    **skill_req
                )
                db.add(db_skill_req)
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error adding job role requirements: {str(e)}")
            db.rollback()
            return
    
    # Check if assessments table is empty
    if db.query(Assessment).count() == 0:
        logger.info("Initializing database with mock assessments")
        assessments_data = get_mock_assessments()
        
        for assessment_data in assessments_data:
            # Extract questions before creating assessment
            questions_data = assessment_data.pop("questions", [])
            
            # Create assessment
            db_assessment = Assessment(**assessment_data)
            db.add(db_assessment)
            
            try:
                db.flush()  # To get the assessment ID
            except Exception as e:
                logger.error(f"Error adding assessment: {str(e)}")
                db.rollback()
                return
            
            # Add questions
            for question_data in questions_data:
                db_question = AssessmentQuestion(
                    assessment_id=db_assessment.id,
                    **question_data
                )
                db.add(db_question)
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error adding assessment questions: {str(e)}")
            db.rollback()
            return

####################################
# Health Check Endpoint
####################################
@app.get("/health")
async def health_check():
    """Health check endpoint for all services"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.app_version
    }

####################################
# Authentication Endpoints
####################################
class TokenRequest(BaseModel):
    username: str
    password: str

@app.post("/token")
def login_for_access_token(form_data: TokenRequest, db: Session = Depends(get_db)):
    """Simple token endpoint for testing"""
    # In a real app, we would check credentials against database
    # For this prototype, we'll accept any username with 'password' as password
    if form_data.password != "password":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Find user or use default
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    if not user:
        user_id = "1"  # Default user ID
        user_role = "user"
    else:
        user_id = str(user.id)
        user_role = "admin" if form_data.username == "admin" else "user"
    
    # Create access token with user ID, role, and scopes
    from middleware import create_access_token
    
    scopes = ["user"]
    if user_role == "admin":
        scopes.extend(["admin", "skills", "assessments", "matches"])
    
    access_token = create_access_token(
        data={
            "sub": user_id, 
            "role": user_role,
            "scopes": scopes
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

####################################
# Skills Service Endpoints
####################################
@app.get("/api/skills/categories", response_model=List[schemas.SkillCategory], tags=["skills"])
def get_skill_categories(
    current_user: User = Security(
        get_current_user_with_scopes,
        scopes=["skills"]
    ),
    db: Session = Depends(get_db)
):
    """Get all skill categories"""
    categories = db.query(SkillCategory).all()
    return categories

@app.get("/api/skills/category/{category_id}", response_model=List[schemas.Skill], tags=["skills"])
def get_skills_by_category(
    category_id: int, 
    current_user: User = Security(
        get_current_user_with_scopes,
        scopes=["skills"]
    ),
    db: Session = Depends(get_db)
):
    """Get all skills in a category"""
    skills = db.query(Skill).filter(Skill.category_id == category_id).all()
    if not skills:
        raise HTTPException(status_code=404, detail="No skills found for this category")
    return skills

@app.get("/api/skills/{skill_id}", response_model=schemas.Skill, tags=["skills"])
def get_skill(
    skill_id: int, 
    current_user: User = Security(
        get_current_user_with_scopes,
        scopes=["skills"]
    ),
    db: Session = Depends(get_db)
):
    """Get a specific skill by ID"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill

@app.post("/api/skills", response_model=schemas.Skill, tags=["skills"])
def create_skill(
    skill: schemas.SkillCreate, 
    current_user: User = Depends(admin_required), 
    db: Session = Depends(get_db)
):
    """Create a new skill"""
    # Check if category exists
    category = db.query(SkillCategory).filter(SkillCategory.id == skill.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Create new skill
    db_skill = Skill(**skill.dict())
    db.add(db_skill)
    
    try:
        db.commit()
        db.refresh(db_skill)
        return db_skill
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating skill: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating skill: {str(e)}")

@app.post("/api/skills/extract", response_model=List[schemas.ExtractedSkill], tags=["skills"])
async def extract_skills_from_text_endpoint(
    text_data: schemas.TextData,
    background_tasks: BackgroundTasks,
    current_user: User = Security(
        get_current_user_with_scopes,
        scopes=["skills"]
    ),
    db: Session = Depends(get_db)
):
    """Extract skills from text using LLM"""
    # Create a copy of the DB session for background tasks
    task_db = next(get_db())
    
    # Log the LLM request
    background_tasks.add_task(
        log_llm_request,
        db=task_db,
        request_type="extract_skills",
        input_data={"text_length": len(text_data.text)}
    )
    
    try:
        # Extract skills from text
        extracted_skills = extract_skills_from_text(text_data.text)
        
        # Log successful response in background
        background_tasks.add_task(
            log_llm_response,
            db=task_db,
            request_type="extract_skills",
            output_data={"skills_found": len(extracted_skills)}
        )
        
        return extracted_skills
    except Exception as e:
        # Log error in background
        background_tasks.add_task(
            log_llm_error,
            db=task_db,
            request_type="extract_skills",
            error_msg=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting skills: {str(e)}"
        )

@app.post("/api/skills/map", response_model=List[schemas.MappedSkill], tags=["skills"])
async def map_skills_to_taxonomy_endpoint(
    skills_list: schemas.SkillsList,
    background_tasks: BackgroundTasks,
    current_user: User = Security(
        get_current_user_with_scopes,
        scopes=["skills"]
    ),
    db: Session = Depends(get_db)
):
    """Map free-text skills to taxonomy"""
    # Get all skills from the database for reference
    db_skills = db.query(Skill).all()
    skill_dict = {skill.name.lower(): skill for skill in db_skills}
    
    # Try exact matching first
    mapped_skills = []
    unmapped_skills = []
    
    for skill in skills_list.skills:
        if skill.lower() in skill_dict:
            db_skill = skill_dict[skill.lower()]
            mapped_skills.append(
                schemas.MappedSkill(
                    original_text=skill,
                    skill_id=db_skill.id,
                    skill_name=db_skill.name,
                    confidence=1.0
                )
            )
        else:
            unmapped_skills.append(skill)
    
    # Create a copy of the DB session for background tasks
    task_db = next(get_db())
    
    # Use LLM to map remaining skills
    if unmapped_skills:
        try:
            # Log the LLM request
            background_tasks.add_task(
                log_llm_request,
                db=task_db,
                request_type="map_skills",
                input_data={"skills": unmapped_skills}
            )
            
            # Map skills to taxonomy
            llm_mapped_skills = map_skills_to_taxonomy(
                unmapped_skills, 
                [s.name for s in db_skills]
            )
            
            # Log successful response
            background_tasks.add_task(
                log_llm_response,
                db=task_db,
                request_type="map_skills",
                output_data={"mapped_count": len(llm_mapped_skills)}
            )
            
            mapped_skills.extend(llm_mapped_skills)
        except Exception as e:
            # Log error
            background_tasks.add_task(
                log_llm_error,
                db=task_db,
                request_type="map_skills",
                error_msg=str(e)
            )
            logger.error(f"Error mapping skills: {str(e)}")
            # Continue with what we have mapped so far
    
    return mapped_skills

@app.get("/api/skills/{skill_id}/related", response_model=List[schemas.RelatedSkill], tags=["skills"])
def get_related_skills(
    skill_id: int, 
    current_user: User = Security(
        get_current_user_with_scopes,
        scopes=["skills"]
    ),
    db: Session = Depends(get_db)
):
    """Get related skills for a specific skill"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Get skills in the same category
    related = db.query(Skill).filter(
        Skill.category_id == skill.category_id,
        Skill.id != skill.id
    ).all()
    
    return [
        schemas.RelatedSkill(
            skill_id=r.id,
            skill_name=r.name,
            relationship_type="same_category",
            relationship_strength=0.8
        ) for r in related
    ]

####################################
# User Service Endpoints
####################################
@app.get("/api/users", response_model=List[schemas.User], tags=["users"])
def get_all_users(
    department: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users with optional filtering"""
    query = db.query(UserModel)
    
    if department:
        query = query.filter(UserModel.department == department)
    
    users = query.offset(skip).limit(limit).all()
    return users

@app.get("/api/users/{user_id}", response_model=schemas.UserDetail, tags=["users"])
def get_user(
    user_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific user by ID"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user skills
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    
    # Get skills details
    skill_details_list = []
    for skill_entry in user_skills:
        # Get skill details
        skill = db.query(Skill).filter(Skill.id == skill_entry.skill_id).first()
        if not skill:
            continue  # Skip if skill not found
            
        # Get category details
        category = db.query(SkillCategory).filter(SkillCategory.id == skill.category_id).first()
        category_name = category.name if category else "Uncategorized"
        
        skill_details_list.append(
            schemas.UserSkillDetail(
                skill_id=skill_entry.skill_id,
                skill_name=skill.name,
                category_id=skill.category_id,
                category_name=category_name,
                proficiency_level=skill_entry.proficiency_level,
                is_verified=skill_entry.is_verified,
                source=skill_entry.source,
                last_verified=skill_entry.last_verified
            )
        )
    
    return schemas.UserDetail(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        department=user.department,
        title=user.title,
        bio=user.bio,
        created_at=user.created_at,
        skills=skill_details_list
    )

@app.post("/api/users", response_model=schemas.User, tags=["users"])
def create_user(
    user_create: schemas.UserCreate, 
    current_user: User = Security(
        get_current_user_with_scopes,
        scopes=["admin"]
    ),
    db: Session = Depends(get_db)
):
    """Create a new user"""
    # Check if username or email already exists
    if db.query(UserModel).filter(UserModel.username == user_create.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    if db.query(UserModel).filter(UserModel.email == user_create.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    db_user = UserModel(**user_create.dict())
    db.add(db_user)
    
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.put("/api/users/{user_id}", response_model=schemas.User, tags=["users"])
def update_user(
    user_id: int, 
    user_update: schemas.UserUpdate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a user"""
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if current user has permission (admin or the user themselves)
    if current_user.role != "admin" and current_user.id != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    
    # Update user fields if provided
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

@app.get("/api/users/{user_id}/skills", response_model=List[schemas.UserSkillDetail], tags=["users"])
async def get_user_skills(
    user_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get skills for a specific user"""
    # Check if user exists
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user skills
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    
    # Get skills details
    skill_details_list = []
    for skill_entry in user_skills:
        # Get skill details
        skill = db.query(Skill).filter(Skill.id == skill_entry.skill_id).first()
        if not skill:
            continue  # Skip if skill not found
            
        # Get category details
        category = db.query(SkillCategory).filter(SkillCategory.id == skill.category_id).first()
        category_name = category.name if category else "Uncategorized"
        
        skill_details_list.append(
            schemas.UserSkillDetail(
                skill_id=skill_entry.skill_id,
                skill_name=skill.name,
                category_id=skill.category_id,
                category_name=category_name,
                proficiency_level=skill_entry.proficiency_level,
                is_verified=skill_entry.is_verified,
                source=skill_entry.source,
                last_verified=skill_entry.last_verified
            )
        )
    
    return skill_details_list

