# skills_service/schemas.py
from pydantic import BaseModel
from typing import List, Optional

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
