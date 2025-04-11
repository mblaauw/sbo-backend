"""
User service endpoints for SBO application.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db
from middleware import get_current_user, admin_required, User
from models import (
    User as UserModel, UserSkill, Skill, SkillCategory
)
import schemas

router = APIRouter(tags=["users"])

@router.get("/users", response_model=List[schemas.User])
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

@router.get("/users/{user_id}", response_model=schemas.UserDetail)
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

@router.post("/users", response_model=schemas.User)
def create_user(
    user_create: schemas.UserCreate, 
    current_user: User = Depends(get_current_user),
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
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/users/{user_id}", response_model=schemas.User)
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
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/{user_id}/skills", response_model=List[schemas.UserSkillDetail])
def get_user_skills(
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

@router.post("/users/{user_id}/skills", response_model=schemas.UserSkillDetail)
def add_user_skill(
    user_id: int, 
    skill_data: schemas.UserSkillCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add or update a skill for a user"""
    # Check if user exists
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if current user has permission (admin or the user themselves)
    if current_user.role != "admin" and current_user.id != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to update this user's skills")
    
    # Check if skill exists
    skill = db.query(Skill).filter(Skill.id == skill_data.skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Check if user already has this skill
    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.skill_id == skill_data.skill_id
    ).first()
    
    try:
        if user_skill:
            # Update existing skill
            user_skill.proficiency_level = skill_data.proficiency_level
            user_skill.is_verified = skill_data.is_verified
            user_skill.source = skill_data.source
            if skill_data.is_verified:
                user_skill.last_verified = datetime.now()
        else:
            # Add new skill
            user_skill = UserSkill(
                user_id=user_id,
                skill_id=skill_data.skill_id,
                proficiency_level=skill_data.proficiency_level,
                is_verified=skill_data.is_verified,
                source=skill_data.source,
                last_verified=datetime.now() if skill_data.is_verified else None
            )
            db.add(user_skill)
        
        db.commit()
        db.refresh(user_skill)
        
        # Get category details
        category = db.query(SkillCategory).filter(SkillCategory.id == skill.category_id).first()
        category_name = category.name if category else "Uncategorized"
        
        return schemas.UserSkillDetail(
            skill_id=skill_data.skill_id,
            skill_name=skill.name,
            category_id=skill.category_id,
            category_name=category_name,
            proficiency_level=skill_data.proficiency_level,
            is_verified=skill_data.is_verified,
            source=skill_data.source,
            last_verified=user_skill.last_verified
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating skill: {str(e)}")

@router.delete("/users/{user_id}/skills/{skill_id}")
def remove_user_skill(
    user_id: int, 
    skill_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a skill from a user"""
    # Check if user exists
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if current user has permission (admin or the user themselves)
    if current_user.role != "admin" and current_user.id != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to update this user's skills")
    
    # Check if user has this skill
    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.skill_id == skill_id
    ).first()
    
    if not user_skill:
        raise HTTPException(status_code=404, detail="User does not have this skill")
    
    try:
        # Remove the skill
        db.delete(user_skill)
        db.commit()
        
        return {"message": "Skill removed successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing skill: {str(e)}")

@router.get("/skills/{skill_id}/users", response_model=List[schemas.UserWithSkill])
def get_users_with_skill(
    skill_id: int, 
    min_proficiency: int = 1,
    verified_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get users who have a specific skill"""
    # Check if skill exists
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Build query
    query = db.query(UserModel, UserSkill).join(
        UserSkill, UserModel.id == UserSkill.user_id
    ).filter(
        UserSkill.skill_id == skill_id,
        UserSkill.proficiency_level >= min_proficiency
    )
    
    if verified_only:
        query = query.filter(UserSkill.is_verified == True)
    
    results = query.all()
    
    # Format results
    users_with_skill = []
    for user, user_skill in results:
        users_with_skill.append(
            schemas.UserWithSkill(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
                department=user.department,
                title=user.title,
                proficiency_level=user_skill.proficiency_level,
                is_verified=user_skill.is_verified,
                source=user_skill.source
            )
        )
    
    return users_with_skill