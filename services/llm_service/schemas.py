# llm_service/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class TextData(BaseModel):
    text: str

class ExtractedSkill(BaseModel):
    skill_name: str
    confidence: float
    context: Optional[str] = None

class MappingRequest(BaseModel):
    skills: List[str]
    taxonomy: List[str]

class MappedSkill(BaseModel):
    original_text: str
    skill_id: int
    skill_name: str
    confidence: float

class AssessmentRequest(BaseModel):
    skill_id: Optional[int] = None
    skill_name: Optional[str] = None
    skill_description: Optional[str] = None
    num_questions: int = 5
    difficulty_level: str = "medium"  # "easy", "medium", "hard"

class AssessmentQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer_index: int
    explanation: str

class AssessmentQuestions(BaseModel):
    skill_id: Optional[int] = None
    skill_name: str
    questions: List[AssessmentQuestion]

class ResumeData(BaseModel):
    text: str

class ResumeSkill(BaseModel):
    name: str
    confidence: float
    evidence: str

class ResumeExperience(BaseModel):
    title: str
    company: Optional[str] = None
    duration: Optional[str] = None
    description: str
    skills: List[str]

class ResumeAnalysis(BaseModel):
    skills: List[ResumeSkill]
    experiences: List[ResumeExperience]
    education: List[Dict[str, Any]]
    summary: str
    suggested_roles: List[str]

class LearningPathRequest(BaseModel):
    user_id: int
    target_skills: List[Dict[str, Any]]
    current_skills: List[Dict[str, Any]]
    time_frame: Optional[str] = None

class LearningPathStep(BaseModel):
    name: str
    description: str
    duration: str
    resources: List[Dict[str, str]]
    skills_addressed: List[str]

class LearningPath(BaseModel):
    user_id: int
    title: str
    description: str
    total_duration: str
    steps: List[LearningPathStep]