

# user_service/schemas.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

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
