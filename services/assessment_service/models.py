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