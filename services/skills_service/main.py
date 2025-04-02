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
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8805")

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

