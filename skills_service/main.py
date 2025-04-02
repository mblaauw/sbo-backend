# skills_service/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
import os
import logging

from .database import get_db, engine
from . import models, schemas
from .mock_data import generate_mock_skills_taxonomy

# Initialize database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Skills Based Organization - Skills Service",
    description="Service for managing skills taxonomy and skills-related operations",
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

# LLM Service URL
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8005")

# Initialize with mock data if needed
@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    if db.query(models.Skill).count() == 0:
        logging.info("Initializing database with mock skills taxonomy")
        skills = generate_mock_skills_taxonomy()
        for skill in skills:
            db_skill = models.Skill(**skill)
            db.add(db_skill)
        db.commit()

# Endpoint to get all skill categories
@app.get("/skills/categories", response_model=List[schemas.SkillCategory])
def get_skill_categories(db: Session = Depends(get_db)):
    categories = db.query(models.SkillCategory).all()
    return categories

# Endpoint to get all skills in a category
@app.get("/skills/category/{category_id}", response_model=List[schemas.Skill])
def get_skills_by_category(category_id: int, db: Session = Depends(get_db)):
    skills = db.query(models.Skill).filter(models.Skill.category_id == category_id).all()
    if not skills:
        raise HTTPException(status_code=404, detail="No skills found for this category")
    return skills

# Endpoint to get a specific skill by ID
@app.get("/skills/{skill_id}", response_model=schemas.Skill)
def get_skill(skill_id: int, db: Session = Depends(get_db)):
    skill = db.query(models.Skill).filter(models.Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill

# Endpoint to create a new skill
@app.post("/skills/", response_model=schemas.Skill)
def create_skill(skill: schemas.SkillCreate, db: Session = Depends(get_db)):
    # Check if category exists
    category = db.query(models.SkillCategory).filter(models.SkillCategory.id == skill.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Create new skill
    db_skill = models.Skill(**skill.dict())
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return db_skill

# Endpoint to extract skills from text using LLM
@app.post("/skills/extract", response_model=List[schemas.ExtractedSkill])
async def extract_skills_from_text(text_data: schemas.TextData):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{LLM_SERVICE_URL}/extract-skills",
                json={"text": text_data.text}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to extract skills from LLM service"
                )
            return response.json()
        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="LLM service unavailable"
            )

# Endpoint to map free-text skills to taxonomy
@app.post("/skills/map", response_model=List[schemas.MappedSkill])
async def map_skills_to_taxonomy(skills: schemas.SkillsList, db: Session = Depends(get_db)):
    # Get all skills from the database for reference
    db_skills = db.query(models.Skill).all()
    skill_dict = {skill.name.lower(): skill for skill in db_skills}
    
    # Try exact matching first
    mapped_skills = []
    unmapped_skills = []
    
    for skill in skills.skills:
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
    
    # Use LLM to map remaining skills
    if unmapped_skills:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{LLM_SERVICE_URL}/map-skills",
                    json={"skills": unmapped_skills, "taxonomy": [s.name for s in db_skills]}
                )
                if response.status_code == 200:
                    llm_mapped_skills = response.json()
                    mapped_skills.extend(llm_mapped_skills)
            except httpx.RequestError:
                # If LLM service fails, return what we could match exactly
                pass
    
    return mapped_skills

# Endpoint to get related skills
@app.get("/skills/{skill_id}/related", response_model=List[schemas.RelatedSkill])
def get_related_skills(skill_id: int, db: Session = Depends(get_db)):
    skill = db.query(models.Skill).filter(models.Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Get skills in the same category
    related = db.query(models.Skill).filter(
        models.Skill.category_id == skill.category_id,
        models.Skill.id != skill.id
    ).all()
    
    return [
        schemas.RelatedSkill(
            skill_id=r.id,
            skill_name=r.name,
            relationship_type="same_category",
            relationship_strength=0.8
        ) for r in related
    ]

# skills_service/models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import relationship

from .database import Base

class SkillCategory(Base):
    __tablename__ = "skill_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    
    skills = relationship("Skill", back_populates="category")

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    statement = Column(String)  # "I can..." statement
    category_id = Column(Integer, ForeignKey("skill_categories.id"))
    
    category = relationship("SkillCategory", back_populates="skills")

# skills_service/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class SkillCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class SkillCategoryCreate(SkillCategoryBase):
    pass

class SkillCategory(SkillCategoryBase):
    id: int
    
    class Config:
        orm_mode = True

class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None
    statement: str
    category_id: int

class SkillCreate(SkillBase):
    pass

class Skill(SkillBase):
    id: int
    
    class Config:
        orm_mode = True

class TextData(BaseModel):
    text: str

class ExtractedSkill(BaseModel):
    skill_name: str
    confidence: float
    context: Optional[str] = None

class SkillsList(BaseModel):
    skills: List[str]

class MappedSkill(BaseModel):
    original_text: str
    skill_id: int
    skill_name: str
    confidence: float

class RelatedSkill(BaseModel):
    skill_id: int
    skill_name: str
    relationship_type: str
    relationship_strength: float

# skills_service/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment or use a default for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skills_service.db")

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

# skills_service/mock_data.py
def generate_mock_skills_taxonomy():
    """Generate mock skills data based on the document's taxonomy"""
    
    skills = [
        # Communicative Skills
        {
            "name": "Speaking",
            "description": "Ability to verbally communicate information clearly",
            "statement": "I can tell something in a way that people understand me.",
            "category_id": 1
        },
        {
            "name": "Persuasive Speaking",
            "description": "Ability to influence or inform an audience",
            "statement": "I can speak persuasively to influence or inform an audience.",
            "category_id": 1
        },
        {
            "name": "Voice Modulation",
            "description": "Ability to adapt voice and intonation to convey emotions",
            "statement": "I can adapt my voice and intonation to effectively convey emotions and intentions.",
            "category_id": 1
        },
        {
            "name": "Information Documentation",
            "description": "Ability to write information so others can understand it",
            "statement": "I can document data so that other people understand it.",
            "category_id": 1
        },
        {
            "name": "Active Listening",
            "description": "Ability to listen and summarize what was said",
            "statement": "I can listen to a conversation and ask targeted questions to gain more information.",
            "category_id": 1
        },
        
        # Cognitive and Analytical Skills
        {
            "name": "Numeracy",
            "description": "Ability to work with numbers and solve numerical problems",
            "statement": "I can calculate and solve problems with numbers.",
            "category_id": 2
        },
        {
            "name": "Rule Application",
            "description": "Ability to apply learned rules to solve problems",
            "statement": "I can use rules I've learned to solve problems.",
            "category_id": 2
        },
        {
            "name": "Scientific Method",
            "description": "Ability to design and conduct experiments",
            "statement": "I can design and conduct experiments to investigate questions.",
            "category_id": 2
        },
        {
            "name": "Data Validation",
            "description": "Ability to assess data reliability",
            "statement": "I can evaluate the reliability of data before using it in my analysis.",
            "category_id": 2
        },
        {
            "name": "Reading Comprehension",
            "description": "Ability to read and understand written text",
            "statement": "I can read and understand written text.",
            "category_id": 2
        },
        {
            "name": "Active Learning",
            "description": "Ability to acquire work-relevant knowledge",
            "statement": "I can acquire knowledge important for my work through thinking, discussing, researching, and creating.",
            "category_id": 2
        },
        {
            "name": "Comparative Analysis",
            "description": "Ability to compare advantages and disadvantages",
            "statement": "I can compare the pros and cons of different options.",
            "category_id": 2
        },
        {
            "name": "Decision Making",
            "description": "Ability to determine the best option",
            "statement": "I can determine what the best option is.",
            "category_id": 2
        },
        {
            "name": "Ethical Reasoning",
            "description": "Ability to integrate ethical considerations in decision-making",
            "statement": "I can integrate ethical considerations in my decision-making process.",
            "category_id": 2
        },
    ]
    
    return skills