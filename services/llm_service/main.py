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

from .database import get_db, engine
from . import models, schemas, llm_client

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
SKILLS_SERVICE_URL = os.getenv("SKILLS_SERVICE_URL", "http://localhost:8101")

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
        extracted = llm_client.extract_skills_from_text(text_data.text)
        
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
        mapped = llm_client.map_skills_to_taxonomy(
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
        questions = llm_client.generate_assessment_questions(
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
        analysis = llm_client.analyze_resume(resume_data.text)
        
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
        learning_path = llm_client.generate_learning_path(
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

# llm_service/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from .database import Base

class LLMRequestLog(Base):
    __tablename__ = "llm_request_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String, index=True)
    input_data = Column(Text)
    timestamp = Column(DateTime(timezone=True))

class LLMResponseLog(Base):
    __tablename__ = "llm_response_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String, index=True)
    output_data = Column(Text)
    timestamp = Column(DateTime(timezone=True))

class LLMErrorLog(Base):
    __tablename__ = "llm_error_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String, index=True)
    error_message = Column(Text)
    timestamp = Column(DateTime(timezone=True))

# llm_service/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class TextData(BaseModel):
    text: str

class ExtractedSkill(BaseModel):
    skill_name: str
    confidence: float
    context: Optional[str] = None

class MappingRequest(BaseModel):
    skills: List[str]
    taxonomy: List[str]

class MappedSkill(BaseModel):
    original_text: str
    skill_id: int
    skill_name: str
    confidence: float

class AssessmentRequest(BaseModel):
    skill_id: Optional[int] = None
    skill_name: Optional[str] = None
    skill_description: Optional[str] = None
    num_questions: int = 5
    difficulty_level: str = "medium"  # "easy", "medium", "hard"

class AssessmentQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer_index: int
    explanation: str

class AssessmentQuestions(BaseModel):
    skill_id: Optional[int] = None
    skill_name: str
    questions: List[AssessmentQuestion]

class ResumeData(BaseModel):
    text: str

class ResumeSkill(BaseModel):
    name: str
    confidence: float
    evidence: str

class ResumeExperience(BaseModel):
    title: str
    company: Optional[str] = None
    duration: Optional[str] = None
    description: str
    skills: List[str]

class ResumeAnalysis(BaseModel):
    skills: List[ResumeSkill]
    experiences: List[ResumeExperience]
    education: List[Dict[str, Any]]
    summary: str
    suggested_roles: List[str]

class LearningPathRequest(BaseModel):
    user_id: int
    target_skills: List[Dict[str, Any]]
    current_skills: List[Dict[str, Any]]
    time_frame: Optional[str] = None

class LearningPathStep(BaseModel):
    name: str
    description: str
    duration: str
    resources: List[Dict[str, str]]
    skills_addressed: List[str]

class LearningPath(BaseModel):
    user_id: int
    title: str
    description: str
    total_duration: str
    steps: List[LearningPathStep]

# llm_service/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment or use a default for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./llm_service.db")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# llm_service/llm_client.py
import os
import json
import logging
from typing import List, Dict, Any
import random

# In a real implementation, this would use an actual LLM API
# For this prototype, we'll mock the responses

def extract_skills_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract skills from unstructured text using an LLM.
    
    Args:
        text: The text to extract skills from
        
    Returns:
        A list of extracted skills with confidence scores and context
    """
    # For the prototype, we'll simulate LLM extraction with predefined skills
    sample_skills = [
        "communication",
        "project management",
        "data analysis",
        "leadership",
        "problem solving",
        "teamwork",
        "programming",
        "public speaking",
        "writing",
        "critical thinking"
    ]
    
    # Mock extraction by randomly selecting skills and generating confidence scores
    text_lower = text.lower()
    extracted_skills = []
    
    for skill in sample_skills:
        if skill in text_lower or random.random() < 0.3:  # Randomly include some skills
            confidence = round(random.uniform(0.7, 0.98), 2)
            context = text[max(0, text_lower.find(skill) - 50):min(len(text), text_lower.find(skill) + 50)] if skill in text_lower else ""
            
            extracted_skills.append({
                "skill_name": skill,
                "confidence": confidence,
                "context": context
            })
    
    return extracted_skills

def map_skills_to_taxonomy(skills: List[str], taxonomy: List[str]) -> List[Dict[str, Any]]:
    """
    Map free-text skills to a standardized taxonomy using an LLM.
    
    Args:
        skills: List of skill names to map
        taxonomy: List of standardized skill names in the taxonomy
        
    Returns:
        A list of mapped skills with confidence scores
    """
    # Mock mapping with simple string matching and random confidence
    mapped_skills = []
    
    for skill in skills:
        best_match = None
        highest_similarity = 0
        
        for tax_skill in taxonomy:
            # Simple string similarity - in a real implementation, use embedding similarity
            similarity = len(set(skill.lower().split()) & set(tax_skill.lower().split())) / max(len(skill.split()), len(tax_skill.split()))
            
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = tax_skill
        
        if highest_similarity > 0.3 or random.random() < 0.8:  # Usually find a match
            confidence = max(0.5, highest_similarity)
            skill_id = taxonomy.index(best_match) + 1  # Mock ID generation
            
            mapped_skills.append({
                "original_text": skill,
                "skill_id": skill_id,
                "skill_name": best_match,
                "confidence": round(confidence, 2)
            })
        else:
            # No good match found - map to a random skill with low confidence
            random_skill = random.choice(taxonomy)
            skill_id = taxonomy.index(random_skill) + 1
            
            mapped_skills.append({
                "original_text": skill,
                "skill_id": skill_id,
                "skill_name": random_skill,
                "confidence": round(random.uniform(0.3, 0.5), 2)
            })
    
    return mapped_skills

def generate_assessment_questions(
    skill_name: str,
    skill_description: str = None,
    num_questions: int = 5,
    difficulty: str = "medium"
) -> List[Dict[str, Any]]:
    """
    Generate assessment questions for a specific skill using an LLM.
    
    Args:
        skill_name: The name of the skill to generate questions for
        skill_description: Optional description of the skill
        num_questions: Number of questions to generate
        difficulty: Difficulty level ("easy", "medium", "hard")
        
    Returns:
        A list of assessment questions with options and correct answers
    """
    # Mock question generation
    questions = []
    
    # Dictionary of question templates by skill
    question_templates = {
        "communication": [
            "What is the most effective way to communicate complex information to a non-technical audience?",
            "When delivering bad news to a team, what approach is most appropriate?",
            "Which of the following is an example of active listening?",
            "What strategy is most effective for resolving a communication conflict?",
            "In a cross-cultural communication context, which factor is most important to consider?"
        ],
        "project management": [
            "What is the critical path in project management?",
            "Which project management methodology is best suited for projects with changing requirements?",
            "What is the purpose of a project kickoff meeting?",
            "How should a project manager address scope creep?",
            "What is the primary purpose of a Gantt chart?"
        ],
        "data analysis": [
            "Which statistical measure is most appropriate for analyzing skewed data?",
            "What is the purpose of data normalization?",
            "Which visualization is best for comparing values across multiple categories?",
            "What is the difference between correlation and causation?",
            "Which sampling method would be most appropriate for a heterogeneous population?"
        ]
    }
    
    # Get templates for the skill or use generic templates
    templates = question_templates.get(skill_name.lower(), [
        f"What is the most important aspect of {skill_name}?",
        f"Which approach to {skill_name} is most effective in a team environment?",
        f"What is a common misconception about {skill_name}?",
        f"How would you measure proficiency in {skill_name}?",
        f"What is the relationship between {skill_name} and organizational performance?"
    ])
    
    # Generate questions based on templates
    for i in range(min(num_questions, len(templates))):
        question = templates[i]
        
        # Generate options
        options = [
            f"Option A for {question}",
            f"Option B for {question}",
            f"Option C for {question}",
            f"Option D for {question}"
        ]
        
        # Randomly select correct answer
        correct_answer = random.randint(0, 3)
        
        questions.append({
            "question": question,
            "options": options,
            "correct_answer_index": correct_answer,
            "explanation": f"Explanation for why option {chr(65 + correct_answer)} is correct for {question}."
        })
    
    return questions

def analyze_resume(resume_text: str) -> Dict[str, Any]:
    """
    Analyze a resume to extract skills, experience, and education.
    
    Args:
        resume_text: The text content of the resume
        
    Returns:
        A dictionary containing extracted information
    """
    # Mock resume analysis
    # Extract potential skills
    skills = extract_skills_from_text(resume_text)
    
    # Mock experiences based on common job titles
    experiences = []
    job_titles = ["Software Engineer", "Project Manager", "Data Analyst", "Marketing Specialist"]
    companies = ["Tech Corp", "Innovative Solutions", "Data Insights", "Marketing Pro"]
    
    for i in range(random.randint(1, 4)):
        title = random.choice(job_titles)
        company = random.choice(companies)
        
        # Assign relevant skills to each experience
        job_skills = []
        for skill in skills:
            if random.random() < 0.5:  # 50% chance to include each skill
                job_skills.append(skill["skill_name"])
        
        experiences.append({
            "title": title,
            "company": company,
            "duration": f"{random.randint(1, 5)} years",
            "description": f"Worked as a {title} at {company}, responsible for various projects and initiatives.",
            "skills": job_skills
        })
    
    # Mock education
    education = [
        {
            "degree": "Bachelor's Degree",
            "field": "Computer Science",
            "institution": "State University",
            "year": str(random.randint(2000, 2020))
        }
    ]
    
    # Generate suggested roles based on extracted skills
    role_mapping = {
        "communication": ["Communications Specialist", "Public Relations Manager"],
        "project management": ["Project Manager", "Program Coordinator"],
        "data analysis": ["Data Analyst", "Business Intelligence Specialist"],
        "leadership": ["Team Lead", "Department Manager"],
        "programming": ["Software Developer", "Web Developer"],
        "public speaking": ["Trainer", "Presenter"],
        "writing": ["Content Writer", "Technical Writer"]
    }
    
    suggested_roles = []
    for skill in skills:
        skill_name = skill["skill_name"].lower()
        if skill_name in role_mapping and random.random() < 0.7:
            suggested_roles.extend(role_mapping[skill_name])
    
    # Remove duplicates and limit to 5 roles
    suggested_roles = list(set(suggested_roles))[:5]
    
    return {
        "skills": skills,
        "experiences": experiences,
        "education": education,
        "summary": f"Experienced professional with skills in {', '.join([s['skill_name'] for s in skills[:3]])}.",
        "suggested_roles": suggested_roles
    }

def generate_learning_path(
    user_id: int,
    target_skills: List[Dict[str, Any]],
    current_skills: List[Dict[str, Any]],
    time_frame: str = None
) -> Dict[str, Any]:
    """
    Generate a personalized learning path to acquire target skills.
    
    Args:
        user_id: The ID of the user
        target_skills: List of skills the user wants to acquire
        current_skills: List of skills the user already has
        time_frame: Optional time constraint
        
    Returns:
        A structured learning path
    """
    # Mock learning path generation
    steps = []
    
    # Create a set of current skill names for easy lookup
    current_skill_names = {skill["name"].lower() for skill in current_skills}
    
    # Filter target skills to those not already possessed
    new_target_skills = [skill for skill in target_skills 
                         if skill["name"].lower() not in current_skill_names]
    
    if not new_target_skills:
        # If all target skills are already possessed, suggest advanced learning
        steps = [
            {
                "name": "Advanced Skill Enhancement",
                "description": "Deepen your existing skills through practical application.",
                "duration": "4 weeks",
                "resources": [
                    {"type": "course", "name": "Advanced Applications in Your Field"}
                ],
                "skills_addressed": [skill["name"] for skill in current_skills[:3]]
            }
        ]
    else:
        # Learning resources by skill type
        resource_templates = {
            "communication": [
                {"type": "course", "name": "Effective Communication in the Workplace"},
                {"type": "book", "name": "How to Win Friends and Influence People"},
                {"type": "workshop", "name": "Active Listening Workshop"}
            ],
            "data analysis": [
                {"type": "course", "name": "Introduction to Data Analysis"},
                {"type": "tutorial", "name": "Python for Data Analysis"},
                {"type": "project", "name": "Analyze a Real-World Dataset"}
            ],
            "project management": [
                {"type": "course", "name": "Project Management Fundamentals"},
                {"type": "certification", "name": "PMI Project Management Professional"},
                {"type": "workshop", "name": "Agile Project Management"}
            ]
        }
        
        # Generate steps for each target skill
        for skill in new_target_skills:
            skill_name = skill["name"].lower()
            
            # Get relevant resources or use generic ones
            resources = resource_templates.get(skill_name, [
                {"type": "course", "name": f"Introduction to {skill['name']}"},
                {"type": "book", "name": f"{skill['name']} in Practice"},
                {"type": "workshop", "name": f"Hands-on {skill['name']}"}
            ])
            
            # Select a subset of resources
            selected_resources = random.sample(resources, min(2, len(resources)))
            
            steps.append({
                "name": f"Learn {skill['name']}",
                "description": f"Develop proficiency in {skill['name']} through structured learning.",
                "duration": f"{random.randint(2, 8)} weeks",
                "resources": selected_resources,
                "skills_addressed": [skill["name"]]
            })
    
    # Calculate total duration
    total_weeks = sum([int(step["duration"].split()[0]) for step in steps])
    
    return {
        "user_id": user_id,
        "title": "Personalized Skill Development Plan",
        "description": f"A customized learning path to help you acquire {len(new_target_skills)} new skills.",
        "total_duration": f"{total_weeks} weeks",
        "steps": steps
    }