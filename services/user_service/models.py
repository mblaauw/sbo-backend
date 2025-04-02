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