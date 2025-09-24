# app/schemas/profile.py
from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional, List
import json

class ProfileBase(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    title: Optional[str] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_username: Optional[str] = None

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    pass

class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    email: Optional[str] = None
    skills: List[str] = []
    is_complete: bool
    completion_percentage: int
    resume_uploaded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
    
    @validator('skills', pre=True)
    def parse_skills(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                return []
        return v or []

class SkillsUpdate(BaseModel):
    skills: List[str]

class ProfileStats(BaseModel):
    profile_completion: int
    total_skills: int
    has_resume: bool
    has_github: bool
    last_updated: Optional[datetime] = None