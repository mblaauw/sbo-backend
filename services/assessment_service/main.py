# assessment_service/main.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import httpx
import os
import logging
from datetime import datetime

from .database import get_db, engine
from . import models, schemas
from .mock_data import generate_mock_assessments

# Initialize database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Skills Based Organization - Assessment Service",
    description="Service for managing skills assessments",
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

# Service URLs
SKILLS_SERVICE_URL = os.getenv("SKILLS_SERVICE_URL", "http://localhost:8101")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8105")

# Initialize with mock data if needed
@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    if db.query(models.Assessment).count() == 0:
        logging.info("Initializing database with mock assessments")
        assessments = generate_mock_assessments()
        for assessment in assessments:
            db_assessment = models.Assessment(
                title=assessment["title"],
                description=assessment["description"],
                skill_id=assessment["skill_id"],
                difficulty_level=assessment["difficulty_level"]
            )
            db.add(db_assessment)
            db.flush()  # To get the assessment ID
            
            # Add questions for this assessment
            for question in assessment["questions"]:
                db_question = models.AssessmentQuestion(
                    assessment_id=db_assessment.id,
                    question_text=question["question_text"],
                    options=question["options"],
                    correct_answer_index=question["correct_answer_index"],
                    explanation=question["explanation"]
                )
                db.add(db_question)
        
        db.commit()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "assessment-service"}

# Endpoint to get all assessments
@app.get("/assessments", response_model=List[schemas.Assessment])
def get_all_assessments(
    skill_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    query = db.query(models.Assessment)
    
    # Apply filters if provided
    if skill_id:
        query = query.filter(models.Assessment.skill_id == skill_id)
    if difficulty:
        query = query.filter(models.Assessment.difficulty_level == difficulty)
    
    assessments = query.offset(skip).limit(limit).all()
    return assessments

# Endpoint to get a specific assessment by ID
@app.get("/assessments/{assessment_id}", response_model=schemas.AssessmentDetail)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Get questions for this assessment
    questions = db.query(models.AssessmentQuestion).filter(
        models.AssessmentQuestion.assessment_id == assessment_id
    ).all()
    
    return schemas.AssessmentDetail(
        id=assessment.id,
        title=assessment.title,
        description=assessment.description,
        skill_id=assessment.skill_id,
        difficulty_level=assessment.difficulty_level,
        questions=[
            schemas.AssessmentQuestionDetail(
                id=q.id,
                question_text=q.question_text,
                options=q.options,
                correct_answer_index=q.correct_answer_index,
                explanation=q.explanation
            ) for q in questions
        ]
    )

# Endpoint to create a new assessment
@app.post("/assessments", response_model=schemas.Assessment)
async def create_assessment(
    assessment_create: schemas.AssessmentCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Check if skill exists in Skills Service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SKILLS_SERVICE_URL}/skills/{assessment_create.skill_id}")
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Skill not found")
            skill = response.json()
    except httpx.RequestError:
        # For prototype, we'll assume the skill exists if Skills Service is unavailable
        skill = {"id": assessment_create.skill_id, "name": f"Skill {assessment_create.skill_id}"}
    
    # Create assessment
    db_assessment = models.Assessment(
        title=assessment_create.title,
        description=assessment_create.description,
        skill_id=assessment_create.skill_id,
        difficulty_level=assessment_create.difficulty_level
    )
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    
    # Generate questions in the background if not provided
    if not assessment_create.questions:
        background_tasks.add_task(
            generate_and_add_questions,
            db,
            db_assessment.id,
            skill["name"] if "name" in skill else f"Skill {assessment_create.skill_id}",
            assessment_create.difficulty_level
        )
    else:
        # Add provided questions
        for question in assessment_create.questions:
            db_question = models.AssessmentQuestion(
                assessment_id=db_assessment.id,
                question_text=question.question_text,
                options=question.options,
                correct_answer_index=question.correct_answer_index,
                explanation=question.explanation
            )
            db.add(db_question)
        db.commit()
    
    return db_assessment

# Endpoint to submit assessment answers and get results
@app.post("/assessments/{assessment_id}/submit", response_model=schemas.AssessmentResult)
def submit_assessment(
    assessment_id: int,
    submission: schemas.AssessmentSubmission,
    db: Session = Depends(get_db)
):
    # Check if assessment exists
    assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Get questions for this assessment
    questions = db.query(models.AssessmentQuestion).filter(
        models.AssessmentQuestion.assessment_id == assessment_id
    ).all()
    
    if len(questions) == 0:
        raise HTTPException(status_code=400, detail="Assessment has no questions")
    
    # Create a map of question IDs to correct answers
    correct_answers = {q.id: q.correct_answer_index for q in questions}
    
    # Calculate score
    num_correct = 0
    question_results = []
    
    for answer in submission.answers:
        if answer.question_id not in correct_answers:
            raise HTTPException(status_code=400, detail=f"Question ID {answer.question_id} not found in assessment")
        
        is_correct = answer.selected_option_index == correct_answers[answer.question_id]
        
        if is_correct:
            num_correct += 1
        
        question_results.append(schemas.QuestionResult(
            question_id=answer.question_id,
            is_correct=is_correct,
            correct_answer_index=correct_answers[answer.question_id]
        ))
    
    # Calculate percentage score
    percentage_score = (num_correct / len(questions)) * 100 if questions else 0
    
    # Determine proficiency level based on score
    proficiency_level = 1  # Default to lowest level
    if percentage_score >= 90:
        proficiency_level = 5
    elif percentage_score >= 80:
        proficiency_level = 4
    elif percentage_score >= 70:
        proficiency_level = 3
    elif percentage_score >= 60:
        proficiency_level = 2
    
    # Save assessment result
    db_result = models.AssessmentResult(
        assessment_id=assessment_id,
        user_id=submission.user_id,
        score=percentage_score,
        proficiency_level=proficiency_level,
        completed_at=datetime.now()
    )
    db.add(db_result)
    db.commit()
    
    return schemas.AssessmentResult(
        id=db_result.id,
        assessment_id=assessment_id,
        user_id=submission.user_id,
        score=percentage_score,
        proficiency_level=proficiency_level,
        question_results=question_results,
        completed_at=db_result.completed_at
    )

# Endpoint to get assessment results for a user
@app.get("/users/{user_id}/assessment-results", response_model=List[schemas.AssessmentResultSummary])
def get_user_assessment_results(user_id: int, db: Session = Depends(get_db)):
    results = db.query(models.AssessmentResult).filter(
        models.AssessmentResult.user_id == user_id
    ).all()
    
    # Get assessment details for each result
    result_summaries = []
    for result in results:
        assessment = db.query(models.Assessment).filter(
            models.Assessment.id == result.assessment_id
        ).first()
        
        if assessment:
            result_summaries.append(schemas.AssessmentResultSummary(
                id=result.id,
                assessment_id=result.assessment_id,
                assessment_title=assessment.title,
                skill_id=assessment.skill_id,
                score=result.score,
                proficiency_level=result.proficiency_level,
                completed_at=result.completed_at
            ))
    
    return result_summaries

# Endpoint to get users who have completed an assessment
@app.get("/assessments/{assessment_id}/users", response_model=List[schemas.UserAssessmentResult])
def get_assessment_user_results(assessment_id: int, db: Session = Depends(get_db)):
    results = db.query(models.AssessmentResult).filter(
        models.AssessmentResult.assessment_id == assessment_id
    ).all()
    
    # In a real implementation, we would fetch user details from User Service
    # For the prototype, we'll return just the user IDs with their scores
    return [
        schemas.UserAssessmentResult(
            user_id=result.user_id,
            score=result.score,
            proficiency_level=result.proficiency_level,
            completed_at=result.completed_at
        ) for result in results
    ]

# Background task to generate and add questions using LLM
async def generate_and_add_questions(
    db: Session,
    assessment_id: int,
    skill_name: str,
    difficulty_level: str,
    num_questions: int = 5
):
    try:
        # Call LLM Service to generate questions
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LLM_SERVICE_URL}/generate-assessment",
                json={
                    "skill_name": skill_name,
                    "num_questions": num_questions,
                    "difficulty_level": difficulty_level
                }
            )
            
            if response.status_code == 200:
                assessment_questions = response.json()
                
                # Add questions to the database
                for question in assessment_questions["questions"]:
                    db_question = models.AssessmentQuestion(
                        assessment_id=assessment_id,
                        question_text=question["question"],
                        options=question["options"],
                        correct_answer_index=question["correct_answer_index"],
                        explanation=question["explanation"]
                    )
                    db.add(db_question)
                
                db.commit()
                logging.info(f"Successfully generated and added {len(assessment_questions['questions'])} questions for assessment {assessment_id}")
            else:
                logging.error(f"Failed to generate questions from LLM Service: {response.text}")
    except Exception as e:
        logging.error(f"Error generating questions: {str(e)}")
        # Add default questions as fallback
        default_questions = [
            {
                "question_text": f"Sample question 1 for {skill_name}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer_index": 0,
                "explanation": "This is a sample explanation for the correct answer."
            },
            {
                "question_text": f"Sample question 2 for {skill_name}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer_index": 1,
                "explanation": "This is a sample explanation for the correct answer."
            }
        ]
        
        for question in default_questions:
            db_question = models.AssessmentQuestion(
                assessment_id=assessment_id,
                question_text=question["question_text"],
                options=question["options"],
                correct_answer_index=question["correct_answer_index"],
                explanation=question["explanation"]
            )
            db.add(db_question)
        
        db.commit()
        logging.info(f"Added default questions for assessment {assessment_id} due to error")

# assessment_service/models.py
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Float, DateTime, ARRAY, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    skill_id = Column(Integer, index=True)  # Reference to skill in Skills Service
    difficulty_level = Column(String)  # "easy", "medium", "hard"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    questions = relationship("AssessmentQuestion", back_populates="assessment")
    results = relationship("AssessmentResult", back_populates="assessment")

class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    question_text = Column(Text)
    options = Column(JSON)  # Store as JSON array
    correct_answer_index = Column(Integer)
    explanation = Column(Text)
    
    assessment = relationship("Assessment", back_populates="questions")

class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"))
    user_id = Column(Integer, index=True)  # Reference to user in User Service
    score = Column(Float)  # Percentage score (0-100)
    proficiency_level = Column(Integer)  # 1-5 skill level achieved
    completed_at = Column(DateTime(timezone=True))
    
    assessment = relationship("Assessment", back_populates="results")

# assessment_service/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class AssessmentQuestionBase(BaseModel):
    question_text: str
    options: List[str]
    correct_answer_index: int
    explanation: str

class AssessmentQuestionCreate(AssessmentQuestionBase):
    pass

class AssessmentQuestionDetail(AssessmentQuestionBase):
    id: int
    
    class Config:
        orm_mode = True

class AssessmentBase(BaseModel):
    title: str
    description: str
    skill_id: int
    difficulty_level: str

class AssessmentCreate(AssessmentBase):
    questions: Optional[List[AssessmentQuestionCreate]] = None

class Assessment(AssessmentBase):
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class AssessmentDetail(Assessment):
    questions: List[AssessmentQuestionDetail]

class QuestionAnswer(BaseModel):
    question_id: int
    selected_option_index: int

class AssessmentSubmission(BaseModel):
    user_id: int
    answers: List[QuestionAnswer]

class QuestionResult(BaseModel):
    question_id: int
    is_correct: bool
    correct_answer_index: int

class AssessmentResult(BaseModel):
    id: int
    assessment_id: int
    user_id: int
    score: float
    proficiency_level: int
    question_results: List[QuestionResult]
    completed_at: datetime
    
    class Config:
        orm_mode = True

class AssessmentResultSummary(BaseModel):
    id: int
    assessment_id: int
    assessment_title: str
    skill_id: int
    score: float
    proficiency_level: int
    completed_at: datetime
    
    class Config:
        orm_mode = True

class UserAssessmentResult(BaseModel):
    user_id: int
    score: float
    proficiency_level: int
    completed_at: datetime
    
    class Config:
        orm_mode = True

# assessment_service/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment or use a default for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./assessment_service.db")

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

# assessment_service/mock_data.py
def generate_mock_assessments():
    """Generate mock assessment data for the assessment service"""
    
    assessments = [
        {
            "title": "Communication Fundamentals",
            "description": "Assessment to evaluate basic communication skills",
            "skill_id": 1,  # Speaking skill ID
            "difficulty_level": "easy",
            "questions": [
                {
                    "question_text": "What is the most effective way to communicate technical information to a non-technical audience?",
                    "options": [
                        "Use technical jargon to sound professional",
                        "Use simple language and analogies",
                        "Provide detailed technical specifications",
                        "Speak quickly to maintain interest"
                    ],
                    "correct_answer_index": 1,
                    "explanation": "When communicating with a non-technical audience, using simple language and analogies helps them understand complex concepts without requiring specialized knowledge."
                },
                {
                    "question_text": "Which of these is an example of active listening?",
                    "options": [
                        "Planning what you'll say next while the other person is speaking",
                        "Looking at your phone occasionally during a conversation",
                        "Interrupting to correct inaccuracies",
                        "Paraphrasing what the speaker said to confirm understanding"
                    ],
                    "correct_answer_index": 3,
                    "explanation": "Active listening involves fully engaging with the speaker and demonstrating understanding, such as by paraphrasing their points."
                },
                {
                    "question_text": "What communication approach is most appropriate when delivering negative feedback?",
                    "options": [
                        "Be direct and critical to ensure the message is clear",
                        "Use a sandwich approach: positive-negative-positive",
                        "Send feedback via email to avoid confrontation",
                        "Focus only on what went wrong"
                    ],
                    "correct_answer_index": 1,
                    "explanation": "The sandwich approach helps deliver constructive criticism in a way that's easier to receive and act upon."
                }
            ]
        },
        {
            "title": "Data Analysis Skills",
            "description": "Assessment to evaluate data analysis capabilities",
            "skill_id": 6,  # Numeracy skill ID
            "difficulty_level": "medium",
            "questions": [
                {
                    "question_text": "What type of chart is best for showing the distribution of a single variable?",
                    "options": [
                        "Pie chart",
                        "Scatter plot",
                        "Histogram",
                        "Line chart"
                    ],
                    "correct_answer_index": 2,
                    "explanation": "Histograms are designed to show the distribution of a single variable, displaying the frequency of data points across different ranges or bins."
                },
                {
                    "question_text": "When analyzing skewed data, which measure of central tendency is most appropriate?",
                    "options": [
                        "Mean",
                        "Median",
                        "Mode",
                        "Range"
                    ],
                    "correct_answer_index": 1,
                    "explanation": "The median is less affected by outliers and skewed distributions than the mean, making it more representative of the center for skewed data."
                },
                {
                    "question_text": "What is the key difference between correlation and causation?",
                    "options": [
                        "Correlation is weaker than causation",
                        "Correlation is always positive, causation can be negative",
                        "Correlation means two variables are related, causation means one variable causes the other",
                        "They are different terms for the same concept"
                    ],
                    "correct_answer_index": 2,
                    "explanation": "Correlation indicates a relationship or association between variables, while causation specifically means that changes in one variable directly cause changes in another."
                }
            ]
        }
    ]
    
    return assessments