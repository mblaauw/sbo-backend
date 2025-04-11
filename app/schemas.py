from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime

# Skills Service Schemas
class SkillCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class SkillCategoryCreate(SkillCategoryBase):
    pass

class SkillCategory(SkillCategoryBase):
    id: int
    
    class Config:
        from_attributes = True

class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None
    statement: str
    category_id: int

class SkillCreate(SkillBase):
    pass

class Skill(SkillBase):
    id: int
    
    class Config:
        from_attributes = True

class TextData(BaseModel):
    text: str

class ExtractedSkill(BaseModel):
    skill_name: str
    confidence: float
    context: Optional[str] = None

class SkillsList(BaseModel):
    skills: List[str]

class MappedSkill(BaseModel):
    original_text: str
    skill_id: int
    skill_name: str
    confidence: float

class RelatedSkill(BaseModel):
    skill_id: int
    skill_name: str
    relationship_type: str
    relationship_strength: float

# User Service Schemas
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

# Matching Service Schemas
class SkillRequirement(BaseModel):
    skill_id: int
    importance: float
    minimum_proficiency: int

class SkillRequirementDetail(SkillRequirement):
    skill_name: str

class JobRoleBase(BaseModel):
    title: str
    description: str
    department: str

class JobRoleCreate(JobRoleBase):
    required_skills: List[SkillRequirement]

class JobRole(JobRoleBase):
    id: int
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class JobRoleDetail(JobRole):
    required_skills: List[SkillRequirementDetail]

class MatchRequest(BaseModel):
    candidate_id: int
    role_id: int

class SkillMatch(BaseModel):
    skill_id: int
    skill_name: str
    required_proficiency: int
    candidate_proficiency: int
    importance: float

class SkillGap(BaseModel):
    skill_id: int
    skill_name: str
    required_proficiency: int
    candidate_proficiency: int
    gap: int
    importance: float

class ExcessSkill(BaseModel):
    skill_id: int
    skill_name: str
    proficiency: int

class TrainingRecommendation(BaseModel):
    skill_id: int
    skill_name: str
    current_level: int
    target_level: int
    training_type: str
    estimated_duration: str

class MatchResult(BaseModel):
    candidate_id: int
    role_id: int
    role_title: str
    overall_match_percentage: float
    skill_matches: List[Dict[str, Any]]
    skill_gaps: List[Dict[str, Any]]
    excess_skills: List[Dict[str, Any]]
    training_recommendations: List[Dict[str, Any]]

class CandidateMatch(BaseModel):
    candidate_id: int
    candidate_name: str
    match_percentage: float
    skill_matches: int
    skill_gaps: int
    excess_skills: int

class RoleMatch(BaseModel):
    role_id: int
    role_title: str
    department: str
    match_percentage: float
    skill_matches: int
    skill_gaps: int
    required_training: str

# Assessment Service Schemas
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

# LLM Service Schemas
class MappingRequest(BaseModel):
    skills: List[str]
    taxonomy: List[str]

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