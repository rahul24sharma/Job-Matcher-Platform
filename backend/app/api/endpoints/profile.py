# app/api/profile.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json

from app.db.session import get_db
from app.core.dependencies import get_current_user, get_current_active_user
from app.db.models import User
from app.services.profile_service import profile_service
from app.schemas.profile import (
    ProfileBase,
    ProfileUpdate,
    ProfileResponse,
    SkillsUpdate,
    ProfileStats
)

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile"""
    profile = profile_service.get_profile_by_user_id(db, current_user.id)
    
    if not profile:
        # Create empty profile if doesn't exist
        from app.db.models import Profile
        profile = Profile(
            user_id=current_user.id,
            full_name=current_user.full_name,
            email=current_user.email
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    # Convert to dict and add email
    profile_data = profile.__dict__
    profile_data['email'] = current_user.email
    return ProfileResponse(**profile_data)

@router.put("/me", response_model=ProfileResponse)
async def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    profile = profile_service.update_profile(db, current_user.id, profile_data)
    profile_data = profile.__dict__
    profile_data['email'] = current_user.email
    return ProfileResponse(**profile_data)

@router.post("/skills", response_model=ProfileResponse)
async def add_skills(
    skills_data: SkillsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add skills to profile"""
    if not skills_data.skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No skills provided"
        )
    
    profile = profile_service.add_skills(db, current_user.id, skills_data.skills)
    profile_data = profile.__dict__
    profile_data['email'] = current_user.email
    return ProfileResponse(**profile_data)

@router.delete("/skills/{skill}")
async def remove_skill(
    skill: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a skill from profile"""
    profile = profile_service.remove_skill(db, current_user.id, skill)
    return {"message": f"Skill '{skill}' removed successfully"}

@router.get("/stats", response_model=ProfileStats)
async def get_profile_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get profile statistics"""
    return profile_service.get_profile_stats(db, current_user.id)

@router.get("/user/{user_id}")
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get another user's public profile"""
    profile = profile_service.get_profile_by_user_id(db, user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return {
        "full_name": profile.full_name,
        "title": profile.title,
        "bio": profile.bio,
        "location": profile.location,
        "skills": json.loads(profile.skills) if profile.skills else [],
        "linkedin_url": profile.linkedin_url,
        "github_username": profile.github_username
    }

@router.delete("/me")
async def delete_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete current user's profile"""
    success = profile_service.delete_profile(db, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return {"message": "Profile deleted successfully"}