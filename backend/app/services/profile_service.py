from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import json
from datetime import datetime

from app.db.models import Profile
from app.db.models import User
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileStats

class ProfileService:
    """Service class for profile-related operations"""
    
    @staticmethod
    def get_profile_by_user_id(db: Session, user_id: int) -> Optional[Profile]:
        """Get profile by user ID"""
        return db.query(Profile).filter(Profile.user_id == user_id).first()
    
    @staticmethod
    def create_profile(db: Session, user_id: int, profile: ProfileCreate) -> Profile:
        """Create a new profile for a user"""
        # Check if profile already exists
        existing_profile = ProfileService.get_profile_by_user_id(db, user_id)
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile already exists for this user"
            )
        
        db_profile = Profile(
            user_id=user_id,
            **profile.dict(exclude_unset=True)
        )
        
        # Calculate completion percentage
        db_profile.completion_percentage = db_profile.calculate_completion()
        db_profile.is_complete = db_profile.completion_percentage >= 80
        
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile
    
    @staticmethod
    def update_profile(
        db: Session, 
        user_id: int, 
        profile_update: ProfileUpdate
    ) -> Profile:
        """Update user profile"""
        profile = ProfileService.get_profile_by_user_id(db, user_id)
        
        if not profile:
            # Create profile if it doesn't exist
            return ProfileService.create_profile(db, user_id, ProfileCreate(**profile_update.dict()))
        
        # Update fields
        update_data = profile_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        # Recalculate completion
        profile.completion_percentage = profile.calculate_completion()
        profile.is_complete = profile.completion_percentage >= 80
        profile.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        return profile
    
    @staticmethod
    def add_skills(
        db: Session, 
        user_id: int, 
        skills: List[str]
    ) -> Profile:
        """Add skills to user profile"""
        profile = ProfileService.get_profile_by_user_id(db, user_id)
        
        if not profile:
            profile = ProfileService.create_profile(
                db, user_id, ProfileCreate()
            )
        
        # Parse existing skills
        existing_skills = []
        if profile.skills:
            try:
                existing_skills = json.loads(profile.skills)
            except json.JSONDecodeError:
                existing_skills = []
        
        # Add new unique skills
        all_skills = list(set(existing_skills + skills))
        profile.skills = json.dumps(all_skills)
        profile.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        return profile
    
    @staticmethod
    def remove_skill(
        db: Session, 
        user_id: int, 
        skill: str
    ) -> Profile:
        """Remove a skill from user profile"""
        profile = ProfileService.get_profile_by_user_id(db, user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        if profile.skills:
            try:
                skills = json.loads(profile.skills)
                if skill in skills:
                    skills.remove(skill)
                    profile.skills = json.dumps(skills)
                    profile.updated_at = datetime.utcnow()
                    db.commit()
                    db.refresh(profile)
            except json.JSONDecodeError:
                pass
        
        return profile
    
    @staticmethod
    def get_profile_stats(db: Session, user_id: int) -> ProfileStats:
        """Get profile statistics"""
        profile = ProfileService.get_profile_by_user_id(db, user_id)
        
        if not profile:
            return ProfileStats(
                profile_completion=0,
                total_skills=0,
                has_resume=False,
                has_github=False,
                last_updated=None
            )
        
        skills_count = 0
        if profile.skills:
            try:
                skills_count = len(json.loads(profile.skills))
            except json.JSONDecodeError:
                skills_count = 0
        
        return ProfileStats(
            profile_completion=profile.completion_percentage,
            total_skills=skills_count,
            has_resume=bool(profile.resume_path),
            has_github=bool(profile.github_username),
            last_updated=profile.updated_at or profile.created_at
        )
    
    @staticmethod
    def delete_profile(db: Session, user_id: int) -> bool:
        """Delete user profile"""
        profile = ProfileService.get_profile_by_user_id(db, user_id)
        
        if not profile:
            return False
        
        db.delete(profile)
        db.commit()
        return True

# Initialize service
profile_service = ProfileService()