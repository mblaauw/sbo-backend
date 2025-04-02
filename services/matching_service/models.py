# matching_service/models.py
from sqlalchemy import Column, ForeignKey, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

class JobRole(Base):
    __tablename__ = "job_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    department = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    skill_requirements = relationship("RoleSkillRequirement", back_populates="role")

class RoleSkillRequirement(Base):
    __tablename__ = "role_skill_requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("job_roles.id"))
    skill_id = Column(Integer, index=True)  # References skill in Skills Service
    importance = Column(Float)  # Weighting factor from 0 to 1
    minimum_proficiency = Column(Integer)  # Required proficiency level (1-5)
    
    role = relationship("JobRole", back_populates="skill_requirements")

class MatchHistory(Base):
    __tablename__ = "match_history"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, index=True)
    role_id = Column(Integer, ForeignKey("job_roles.id"))
    match_percentage = Column(Float)
    match_date = Column(DateTime(timezone=True), server_default=func.now())
    
    role = relationship("JobRole")

