from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

#######################
# Skills Service Models
#######################
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

#####################
# User Service Models
#####################
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

#########################
# Matching Service Models
#########################
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

###########################
# Assessment Service Models
###########################
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

######################
# LLM Service Models
######################
class LLMRequestLog(Base):
    __tablename__ = "llm_request_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String, index=True)
    input_data = Column(Text)
    timestamp = Column(DateTime(timezone=True))

class LLMResponseLog(Base):
    __tablename__ = "llm_response_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String, index=True)
    output_data = Column(Text)
    timestamp = Column(DateTime(timezone=True))

class LLMErrorLog(Base):
    __tablename__ = "llm_error_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String, index=True)
    error_message = Column(Text)
    timestamp = Column(DateTime(timezone=True))
