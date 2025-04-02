# user_service/main.py
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
from .mock_data import generate_mock_users

# Initialize database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Skills Based Organization - User Service",
    description="Service for managing user profiles and their skills",
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
SKILLS_SERVICE_URL = os.getenv("SKILLS_SERVICE_URL", "http://localhost:8801")
ASSESSMENT_SERVICE_URL = os.getenv("ASSESSMENT_SERVICE_URL", "http://localhost:8804")

# Initialize with mock data if needed
@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    if db.query(models.User).count() == 0:
        logging.info("Initializing database with mock users")
        mock_users = generate_mock_users()
        
        for user_data in mock_users:
            # Create user
            user = models.User(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                department=user_data["department"],
                title=user_data["title"],
                bio=user_data["bio"]
            )
            db.add(user)
            db.flush()  # To get the user ID
            
            # Add skills
            for skill_data in user_data["skills"]:
                user_skill = models.UserSkill(
                    user_id=user.id,
                    skill_id=skill_data["skill_id"],
                    proficiency_level=skill_data["proficiency_level"],
                    is_verified=skill_data["is_verified"],
                    source=skill_data["source"]
                )
                db.add(user_skill)
        
        db.commit()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}

# Endpoint to get all users
@app.get("/users", response_model=List[schemas.User])
def get_all_users(
    department: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    query = db.query(models.User)
    
    # Apply filters if provided
    if department:
        query = query.filter(models.User.department == department)
    
    users = query.offset(skip).limit(limit).all()
    return users

# Endpoint to get a specific user by ID
@app.get("/users/{user_id}", response_model=schemas.UserDetail)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user skills
    user_skills = db.query(models.UserSkill).filter(models.UserSkill.user_id == user_id).all()
    
    # Get skill details from Skills Service in a real implementation
    # For this prototype, we'll use mock skill names
    skill_details = {}
    
    skill_categories = {
        1: "Communication",
        2: "Cognitive",
        3: "Technical",
        4: "Leadership",
        5: "Project Management"
    }
    
    for skill in user_skills:
        category_id = (skill.skill_id % 5) + 1  # Mock category ID
        skill_details[skill.skill_id] = {
            "id": skill.skill_id,
            "name": f"Skill {skill.skill_id}",
            "category_id": category_id,
            "category_name": skill_categories.get(category_id, "Other")
        }
    
    # Construct UserSkillDetail objects
    skill_details_list = []
    for skill in user_skills:
        detail = skill_details.get(skill.skill_id, {"name": f"Unknown Skill {skill.skill_id}"})
        skill_details_list.append(
            schemas.UserSkillDetail(
                skill_id=skill.skill_id,
                skill_name=detail.get("name", ""),
                category_id=detail.get("category_id"),
                category_name=detail.get("category_name", ""),
                proficiency_level=skill.proficiency_level,
                is_verified=skill.is_verified,
                source=skill.source,
                last_verified=skill.last_verified
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

# Endpoint to create a new user
@app.post("/users", response_model=schemas.User)
def create_user(user_create: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    if db.query(models.User).filter(models.User.username == user_create.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    if db.query(models.User).filter(models.User.email == user_create.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    db_user = models.User(
        username=user_create.username,
        email=user_create.email,
        full_name=user_create.full_name,
        department=user_create.department,
        title=user_create.title,
        bio=user_create.bio
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Endpoint to update a user
@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user fields
    if user_update.email:
        db_user.email = user_update.email
    if user_update.full_name:
        db_user.full_name = user_update.full_name
    if user_update.department:
        db_user.department = user_update.department
    if user_update.title:
        db_user.title = user_update.title
    if user_update.bio:
        db_user.bio = user_update.bio
    
    db.commit()
    db.refresh(db_user)
    return db_user

# Endpoint to get user skills
@app.get("/users/{user_id}/skills", response_model=List[schemas.UserSkillDetail])
async def get_user_skills(user_id: int, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user skills
    user_skills = db.query(models.UserSkill).filter(models.UserSkill.user_id == user_id).all()
    
    # Get skill details from Skills Service
    # In a real implementation, we would call the Skills Service API
    # For this prototype, we use mock skill details
    skill_categories = {
        1: "Communication",
        2: "Cognitive",
        3: "Technical",
        4: "Leadership",
        5: "Project Management"
    }
    
    skill_details_list = []
    for skill in user_skills:
        category_id = (skill.skill_id % 5) + 1  # Mock category ID
        skill_details_list.append(
            schemas.UserSkillDetail(
                skill_id=skill.skill_id,
                skill_name=f"Skill {skill.skill_id}",
                category_id=category_id,
                category_name=skill_categories.get(category_id, "Other"),
                proficiency_level=skill.proficiency_level,
                is_verified=skill.is_verified,
                source=skill.source,
                last_verified=skill.last_verified
            )
        )
    
    return skill_details_list

# Endpoint to add or update a user skill
@app.post("/users/{user_id}/skills", response_model=schemas.UserSkillDetail)
async def add_user_skill(
    user_id: int, 
    skill_data: schemas.UserSkillCreate, 
    db: Session = Depends(get_db)
):
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if skill exists in Skills Service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SKILLS_SERVICE_URL}/skills/{skill_data.skill_id}")
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Skill not found")
            skill = response.json()
    except httpx.RequestError:
        # For prototype, we'll assume the skill exists if Skills Service is unavailable
        skill = {"id": skill_data.skill_id, "name": f"Skill {skill_data.skill_id}"}
    
    # Check if user already has this skill
    user_skill = db.query(models.UserSkill).filter(
        models.UserSkill.user_id == user_id,
        models.UserSkill.skill_id == skill_data.skill_id
    ).first()
    
    if user_skill:
        # Update existing skill
        user_skill.proficiency_level = skill_data.proficiency_level
        user_skill.is_verified = skill_data.is_verified
        user_skill.source = skill_data.source
        if skill_data.is_verified:
            user_skill.last_verified = datetime.now()
    else:
        # Add new skill
        user_skill = models.UserSkill(
            user_id=user_id,
            skill_id=skill_data.skill_id,
            proficiency_level=skill_data.proficiency_level,
            is_verified=skill_data.is_verified,
            source=skill_data.source,
            last_verified=datetime.now() if skill_data.is_verified else None
        )
        db.add(user_skill)
    
    db.commit()
    
    # Create response with skill details
    category_id = (skill_data.skill_id % 5) + 1  # Mock category ID
    skill_categories = {
        1: "Communication",
        2: "Cognitive",
        3: "Technical",
        4: "Leadership",
        5: "Project Management"
    }
    
    return schemas.UserSkillDetail(
        skill_id=skill_data.skill_id,
        skill_name=skill.get("name", f"Skill {skill_data.skill_id}"),
        category_id=category_id,
        category_name=skill_categories.get(category_id, "Other"),
        proficiency_level=skill_data.proficiency_level,
        is_verified=skill_data.is_verified,
        source=skill_data.source,
        last_verified=user_skill.last_verified
    )

# Endpoint to remove a user skill
@app.delete("/users/{user_id}/skills/{skill_id}")
def remove_user_skill(user_id: int, skill_id: int, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user has this skill
    user_skill = db.query(models.UserSkill).filter(
        models.UserSkill.user_id == user_id,
        models.UserSkill.skill_id == skill_id
    ).first()
    
    if not user_skill:
        raise HTTPException(status_code=404, detail="User does not have this skill")
    
    # Remove the skill
    db.delete(user_skill)
    db.commit()
    
    return {"message": "Skill removed successfully"}

# Endpoint to get users with a specific skill
@app.get("/skills/{skill_id}/users", response_model=List[schemas.UserWithSkill])
def get_users_with_skill(
    skill_id: int, 
    min_proficiency: int = 1,
    verified_only: bool = False,
    db: Session = Depends(get_db)
):
    # Build query based on parameters
    query = db.query(models.User, models.UserSkill).join(
        models.UserSkill, models.User.id == models.UserSkill.user_id
    ).filter(
        models.UserSkill.skill_id == skill_id,
        models.UserSkill.proficiency_level >= min_proficiency
    )
    
    if verified_only:
        query = query.filter(models.UserSkill.is_verified == True)
    
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

# Endpoint to sync assessment results
@app.post("/sync-assessment-results")
async def sync_assessment_results(background_tasks: BackgroundTasks):
    # This would be a scheduled task in a real implementation
    # For the prototype, we'll trigger it manually
    
    background_tasks.add_task(sync_all_assessment_results)
    
    return {"message": "Assessment result sync started in the background"}

# Background task to sync assessment results
async def sync_all_assessment_results():
    db = next(get_db())
    
    try:
        # Get all users
        users = db.query(models.User).all()
        
        async with httpx.AsyncClient() as client:
            for user in users:
                try:
                    # Get assessment results for this user
                    response = await client.get(
                        f"{ASSESSMENT_SERVICE_URL}/users/{user.id}/assessment-results"
                    )
                    
                    if response.status_code == 200:
                        assessment_results = response.json()
                        
                        # Update or add skills based on assessment results
                        for result in assessment_results:
                            skill_id = result.get("skill_id")
                            proficiency_level = result.get("proficiency_level")
                            
                            if skill_id and proficiency_level:
                                # Check if user already has this skill
                                user_skill = db.query(models.UserSkill).filter(
                                    models.UserSkill.user_id == user.id,
                                    models.UserSkill.skill_id == skill_id
                                ).first()
                                
                                if user_skill:
                                    # Update only if assessment shows higher proficiency
                                    if proficiency_level > user_skill.proficiency_level:
                                        user_skill.proficiency_level = proficiency_level
                                        user_skill.is_verified = True
                                        user_skill.source = "assessment"
                                        user_skill.last_verified = datetime.now()
                                else:
                                    # Add new skill
                                    user_skill = models.UserSkill(
                                        user_id=user.id,
                                        skill_id=skill_id,
                                        proficiency_level=proficiency_level,
                                        is_verified=True,
                                        source="assessment",
                                        last_verified=datetime.now()
                                    )
                                    db.add(user_skill)
                        
                        db.commit()
                        logging.info(f"Synced assessment results for user {user.id}")
                        
                except Exception as e:
                    logging.error(f"Error syncing assessment results for user {user.id}: {str(e)}")
    except Exception as e:
        logging.error(f"Error in assessment result sync: {str(e)}")
    finally:
        db.close()

# user_service/models.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    department = Column(String, index=True)
    title = Column(String)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    skills = relationship("UserSkill", back_populates="user")

class UserSkill(Base):
    __tablename__ = "user_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    skill_id = Column(Integer, index=True)  # Reference to skill in Skills Service
    proficiency_level = Column(Integer)  # 1-5 scale
    is_verified = Column(Boolean, default=False)
    source = Column(String)  # 'self-assessment', 'manager', 'peer', 'assessment', 'resume'
    last_verified = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User", back_populates="skills")

# user_service/schemas.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    department: Optional[str] = None
    title: Optional[str] = None
    bio: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    bio: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserSkillBase(BaseModel):
    skill_id: int
    proficiency_level: int
    is_verified: bool = False
    source: str

class UserSkillCreate(UserSkillBase):
    pass

class UserSkillDetail(UserSkillBase):
    skill_name: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    last_verified: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserDetail(User):
    skills: List[UserSkillDetail]

class UserWithSkill(BaseModel):
    id: int
    username: str
    full_name: str
    department: Optional[str] = None
    title: Optional[str] = None
    proficiency_level: int
    is_verified: bool
    source: str
    
    class Config:
        from_attributes = True

# user_service/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment or use a default for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./user_service.db")

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

# user_service/mock_data.py
def generate_mock_users():
    """Generate mock user data for the user service"""
    
    users = [
        {
            "username": "johndoe",
            "email": "john.doe@example.com",
            "full_name": "John Doe",
            "department": "Engineering",
            "title": "Software Engineer",
            "bio": "Experienced software engineer with a passion for building scalable applications.",
            "skills": [
                {"skill_id": 1, "proficiency_level": 4, "is_verified": True, "source": "assessment"},
                {"skill_id": 5, "proficiency_level": 3, "is_verified": True, "source": "manager"},
                {"skill_id": 7, "proficiency_level": 5, "is_verified": True, "source": "assessment"},
                {"skill_id": 9, "proficiency_level": 3, "is_verified": False, "source": "self-assessment"}
            ]
        },
        {
            "username": "janesmith",
            "email": "jane.smith@example.com",
            "full_name": "Jane Smith",
            "department": "Marketing",
            "title": "Marketing Manager",
            "bio": "Creative marketing professional with expertise in digital campaigns.",
            "skills": [
                {"skill_id": 2, "proficiency_level": 5, "is_verified": True, "source": "assessment"},
                {"skill_id": 3, "proficiency_level": 4, "is_verified": True, "source": "peer"},
                {"skill_id": 5, "proficiency_level": 4, "is_verified": True, "source": "manager"},
                {"skill_id": 11, "proficiency_level": 3, "is_verified": False, "source": "self-assessment"}
            ]
        },
        {
            "username": "robertjohnson",
            "email": "robert.johnson@example.com",
            "full_name": "Robert Johnson",
            "department": "Operations",
            "title": "Project Manager",
            "bio": "Certified project manager with experience in agile methodologies.",
            "skills": [
                {"skill_id": 5, "proficiency_level": 5, "is_verified": True, "source": "assessment"},
                {"skill_id": 8, "proficiency_level": 4, "is_verified": True, "source": "manager"},
                {"skill_id": 13, "proficiency_level": 4, "is_verified": True, "source": "assessment"},
                {"skill_id": 2, "proficiency_level": 3, "is_verified": False, "source": "self-assessment"}
            ]
        }
    ]
    
    return users