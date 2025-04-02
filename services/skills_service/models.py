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



