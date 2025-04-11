"""
Skills service endpoints for SBO application.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import logging

from database import get_db
from middleware import get_current_user, admin_required, User
from models import (
    SkillCategory, Skill
)
import schemas
from utils.llm_utils import log_llm_request, log_llm_response, log_llm_error

logger = logging.getLogger("sbo.skills_routes")

router = APIRouter(prefix="/skills", tags=["skills"])

@router.get("/categories", response_model=List[schemas.SkillCategory])
def get_skill_categories(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all skill categories"""
    categories = db.query(SkillCategory).all()
    return categories

@router.get("/category/{category_id}", response_model=List[schemas.Skill])
def get_skills_by_category(
    category_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all skills in a category"""
    skills = db.query(Skill).filter(Skill.category_id == category_id).all()
    if not skills:
        raise HTTPException(status_code=404, detail="No skills found for this category")
    return skills

@router.get("/{skill_id}", response_model=schemas.Skill)
def get_skill(
    skill_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific skill by ID"""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill

@router.post("/", response_model=schemas.Skill)
def create_skill(
    skill: schemas.SkillCreate,
    user: User = Depends(admin_required),
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
    db.commit()
    db.refresh(db_skill)
    return db_skill

@router.post("/extract", response_model=List[schemas.ExtractedSkill])
async def extract_skills_from_text(
    text_data: schemas.TextData,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Extract skills from text using LLM"""
    # Log the LLM request
    background_tasks.add_task(
        log_llm_request,
        request_type="extract_skills",
        input_data={"text_length": len(text_data.text)}
    )

    try:
        # Import here to avoid circular import
        from mock_data import extract_skills_from_text
        extracted_skills = extract_skills_from_text(text_data.text)

        # Log successful response
        background_tasks.add_task(
            log_llm_response,
            request_type="extract_skills",
            output_data={"skills_found": len(extracted_skills)}
        )

        return extracted_skills
    except Exception as e:
        # Log error
        background_tasks.add_task(
            log_llm_error,
            request_type="extract_skills",
            error_msg=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting skills: {str(e)}"
        )

@router.post("/map", response_model=List[schemas.MappedSkill])
async def map_skills_to_taxonomy(
    skills: schemas.SkillsList,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Map free-text skills to taxonomy"""
    # Get all skills from the database for reference
    db_skills = db.query(Skill).all()
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
        try:
            # Log the LLM request
            background_tasks.add_task(
                log_llm_request,
                request_type="map_skills",
                input_data={"skills": unmapped_skills}
            )

            # Import here to avoid circular import
            from mock_data import map_skills_to_taxonomy
            llm_mapped_skills = map_skills_to_taxonomy(
                unmapped_skills,
                [s.name for s in db_skills]
            )

            # Log successful response
            background_tasks.add_task(
                log_llm_response,
                request_type="map_skills",
                output_data={"mapped_count": len(llm_mapped_skills)}
            )

            mapped_skills.extend(llm_mapped_skills)
        except Exception as e:
            # Log error
            background_tasks.add_task(
                log_llm_error,
                request_type="map_skills",
                error_msg=str(e)
            )
            logger.error(f"Error mapping skills: {str(e)}")
            # Continue with what we have mapped so far

    return mapped_skills

@router.get("/{skill_id}/related", response_model=List[schemas.RelatedSkill])
def get_related_skills(
    skill_id: int,
    user: User = Depends(get_current_user),
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
