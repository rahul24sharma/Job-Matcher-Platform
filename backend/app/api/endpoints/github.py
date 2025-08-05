# app/api/endpoints/github.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import User, Skill
from app.core.dependencies import get_current_active_user
from app.services.github_analyzer import GitHubAnalyzer
import logging

router = APIRouter(prefix="/github", tags=["github"])
logger = logging.getLogger(__name__)

# Request/Response models
class GitHubConnectRequest(BaseModel):
    username: str

class GitHubProfileResponse(BaseModel):
    username: str
    profile: Dict
    languages: Dict[str, int]
    skills: list[str]
    top_repositories: list[Dict]
    activity_score: float
    total_stars: int
    total_forks: int

class MessageResponse(BaseModel):
    message: str
    data: Optional[Dict] = None

# Background task function
def analyze_github_background(user_id: int, username: str, db: Session):
    """Background task to analyze GitHub profile"""
    try:
        # Create analyzer
        analyzer = GitHubAnalyzer(db)
        
        # Analyze profile
        result = analyzer.analyze_profile(username)
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        # Update user's GitHub username
        user.github_username = username
        
        # Delete existing GitHub skills for this user
        db.query(Skill).filter(
            Skill.user_id == user_id,
            Skill.name.like('github_%')
        ).delete()
        
        # Add new skills with 'github_' prefix to distinguish source
        for skill_name in result['skills']:
            skill = Skill(
                name=f"github_{skill_name}",
                user_id=user_id
            )
            db.add(skill)
        
        db.commit()
        logger.info(f"Successfully analyzed GitHub profile for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in background GitHub analysis: {str(e)}")
        db.rollback()

@router.post("/connect", response_model=MessageResponse)
async def connect_github(
    request: GitHubConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Connect GitHub account and analyze immediately (no background task)
    """
    # Check if username is already taken by another user
    existing = db.query(User).filter(
        User.github_username == request.username,
        User.id != current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="This GitHub username is already connected to another account"
        )
    
    try:
        # Update user's GitHub username FIRST
        current_user.github_username = request.username
        db.commit()
        
        # Create analyzer
        analyzer = GitHubAnalyzer(db)
        
        # Analyze profile (synchronously)
        result = analyzer.analyze_profile(request.username)
        
        # Delete existing GitHub skills for this user
        db.query(Skill).filter(
            Skill.user_id == current_user.id,
            Skill.name.like('github_%')
        ).delete()
        
        # Add new skills with 'github_' prefix
        for skill_name in result['skills']:
            skill = Skill(
                name=f"github_{skill_name}",
                user_id=current_user.id
            )
            db.add(skill)
        
        db.commit()
        
        return {
            "message": f"GitHub account {request.username} connected and analyzed successfully.",
            "data": {
                "username": request.username,
                "skills_found": len(result['skills']),
                "languages": list(result['languages'].keys()),
                "activity_score": result['activity_score']
            }
        }
        
    except ValueError as e:
        # GitHub user not found
        current_user.github_username = None  # Reset on error
        db.commit()
        raise HTTPException(status_code=404, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error analyzing GitHub profile: {str(e)}")
        current_user.github_username = None  # Reset on error
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze GitHub profile: {str(e)}"
        )

@router.get("/profile", response_model=Optional[GitHubProfileResponse])
async def get_github_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's GitHub profile analysis
    """
    if not current_user.github_username:
        return None
    
    try:
        # Get fresh analysis
        analyzer = GitHubAnalyzer(db)
        result = analyzer.analyze_profile(current_user.github_username)
        return result
        
    except Exception as e:
        logger.error(f"Error fetching GitHub profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch GitHub profile"
        )

@router.post("/analyze", response_model=GitHubProfileResponse)
async def analyze_github_now(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Trigger immediate GitHub analysis (synchronous)
    """
    if not current_user.github_username:
        raise HTTPException(
            status_code=400,
            detail="No GitHub username connected. Please connect first."
        )
    
    try:
        # Analyze profile
        analyzer = GitHubAnalyzer(db)
        result = analyzer.analyze_profile(current_user.github_username)
        
        # Update skills in database
        # Delete existing GitHub skills
        db.query(Skill).filter(
            Skill.user_id == current_user.id,
            Skill.name.like('github_%')
        ).delete()
        
        # Add new skills
        for skill_name in result['skills']:
            skill = Skill(
                name=f"github_{skill_name}",
                user_id=current_user.id
            )
            db.add(skill)
        
        db.commit()
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing GitHub profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze GitHub profile"
        )

@router.get("/skills")
async def get_github_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get skills extracted from GitHub
    """
    # Get GitHub skills (those prefixed with 'github_')
    github_skills = db.query(Skill).filter(
        Skill.user_id == current_user.id,
        Skill.name.like('github_%')
    ).all()
    
    # Remove prefix for display
    skills = [skill.name.replace('github_', '') for skill in github_skills]
    
    return {
        "skills": skills,
        "total": len(skills),
        "github_username": current_user.github_username
    }

@router.get("/all-skills")
async def get_all_user_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all skills from resume and GitHub combined
    """
    # Get all skills
    all_skills = db.query(Skill).filter(Skill.user_id == current_user.id).all()
    
    resume_skills = []
    github_skills = []
    
    for skill in all_skills:
        if skill.name.startswith('github_'):
            github_skills.append(skill.name.replace('github_', ''))
        else:
            resume_skills.append(skill.name)
    
    # Find common skills
    common_skills = list(set(resume_skills) & set(github_skills))
    
    # All unique skills
    all_unique = list(set(resume_skills + github_skills))
    
    return {
        "resume_skills": sorted(resume_skills),
        "github_skills": sorted(github_skills),
        "common_skills": sorted(common_skills),
        "all_skills": sorted(all_unique),
        "total_unique": len(all_unique),
        "stats": {
            "resume_only": len(resume_skills) - len(common_skills),
            "github_only": len(github_skills) - len(common_skills),
            "both": len(common_skills)
        }
    }

@router.delete("/disconnect")
async def disconnect_github(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Disconnect GitHub account
    """
    # Remove GitHub username
    current_user.github_username = None
    
    # Delete GitHub skills
    db.query(Skill).filter(
        Skill.user_id == current_user.id,
        Skill.name.like('github_%')
    ).delete()
    
    db.commit()
    
    return {"message": "GitHub account disconnected successfully"}