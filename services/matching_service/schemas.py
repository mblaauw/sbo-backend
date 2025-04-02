# matching_service/schemas.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

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