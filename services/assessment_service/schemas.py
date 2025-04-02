# assessment_service/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class AssessmentQuestionBase(BaseModel):
    question_text: str
    options: List[str]
    correct_answer_index: int
    explanation: str

class AssessmentQuestionCreate(AssessmentQuestionBase):
    pass

class AssessmentQuestionDetail(AssessmentQuestionBase):
    id: int
    
    class Config:
        from_attributes = True

class AssessmentBase(BaseModel):
    title: str
    description: str
    skill_id: int
    difficulty_level: str

class AssessmentCreate(AssessmentBase):
    questions: Optional[List[AssessmentQuestionCreate]] = None

class Assessment(AssessmentBase):
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AssessmentDetail(Assessment):
    questions: List[AssessmentQuestionDetail]

class QuestionAnswer(BaseModel):
    question_id: int
    selected_option_index: int

class AssessmentSubmission(BaseModel):
    user_id: int
    answers: List[QuestionAnswer]

class QuestionResult(BaseModel):
    question_id: int
    is_correct: bool
    correct_answer_index: int

class AssessmentResult(BaseModel):
    id: int
    assessment_id: int
    user_id: int
    score: float
    proficiency_level: int
    question_results: List[QuestionResult]
    completed_at: datetime
    
    class Config:
        from_attributes = True

class AssessmentResultSummary(BaseModel):
    id: int
    assessment_id: int
    assessment_title: str
    skill_id: int
    score: float
    proficiency_level: int
    completed_at: datetime
    
    class Config:
        from_attributes = True

class UserAssessmentResult(BaseModel):
    user_id: int
    score: float
    proficiency_level: int
    completed_at: datetime
    
    class Config:
        from_attributes = True