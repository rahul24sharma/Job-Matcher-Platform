import logging
from datetime import datetime
from typing import Dict, Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, Skill, TaskStatus
from app.core.dependencies import get_current_active_user
from app.services.github_analyzer import GitHubAnalyzer

router = APIRouter(prefix="/github", tags=["github"])
logger = logging.getLogger(__name__)

# -------------------------
# Schemas
# -------------------------
class GitHubConnectRequest(BaseModel):
    username: str

class GitHubProfileResponse(BaseModel):
    username: str
    profile: Dict
    languages: Dict[str, int]
    skills: List[str]
    top_repositories: List[Dict]
    activity_score: float
    total_stars: int
    total_forks: int

class MessageResponse(BaseModel):
    message: str
    data: Optional[Dict] = None

# -------------------------
# Simple cache using TaskStatus (no schema changes)
# -------------------------
def save_profile_cache(db: Session, user_id: int, result: dict):
    db.add(TaskStatus(
        user_id=user_id,
        task_type="github_profile",
        status="completed",
        result=result,
        completed_at=datetime.utcnow(),
    ))
    db.commit()

def get_profile_cache(db: Session, user_id: int):
    row = (
        db.query(TaskStatus)
        .filter(
            TaskStatus.user_id == user_id,
            TaskStatus.task_type == "github_profile",
            TaskStatus.status == "completed",
        )
        .order_by(TaskStatus.created_at.desc())
        .first()
    )
    return row.result if row else None

# -------------------------
# Endpoints
# -------------------------
@router.post("/connect", response_model=MessageResponse)
async def connect_github(
    request: GitHubConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Connect GitHub account and analyze immediately (synchronous).
    """
    # Unique username guard
    existing = (
        db.query(User)
        .filter(User.github_username == request.username, User.id != current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="This GitHub username is already connected to another account",
        )

    try:
        # Save username first
        current_user.github_username = request.username
        db.commit()

        analyzer = GitHubAnalyzer(db)
        result = analyzer.analyze_profile(request.username)

        # Replace github_* skills for this user
        db.query(Skill).filter(
            Skill.user_id == current_user.id, Skill.name.like("github_%")
        ).delete()

        for sk in result["skills"]:
            db.add(Skill(name=f"github_{sk}", user_id=current_user.id))
        db.commit()

        # Cache the full result for fast GET /profile
        save_profile_cache(db, current_user.id, result)

        return {
            "message": f"GitHub account {request.username} connected and analyzed successfully.",
            "data": {
                "username": request.username,
                "skills_found": len(result["skills"]),
                "languages": list(result["languages"].keys()),
                "activity_score": result["activity_score"],
            },
        }

    except ValueError as e:
        current_user.github_username = None
        db.commit()
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"Error analyzing GitHub profile: {str(e)}")
        current_user.github_username = None
        db.commit()
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze GitHub profile: {str(e)}"
        )

@router.get("/profile", response_model=Optional[GitHubProfileResponse])
async def get_github_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    FAST: return last cached analysis (do NOT re-analyze here).
    """
    if not current_user.github_username:
        return None

    cached = get_profile_cache(db, current_user.id)
    return cached  # may be None if never analyzed

@router.post("/analyze", response_model=GitHubProfileResponse)
async def analyze_github_now(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Recompute analysis now (synchronous), update skills & cache.
    """
    if not current_user.github_username:
        raise HTTPException(
            status_code=400, detail="No GitHub username connected. Please connect first."
        )

    try:
        analyzer = GitHubAnalyzer(db)
        result = analyzer.analyze_profile(current_user.github_username)

        # Replace github_* skills
        db.query(Skill).filter(
            Skill.user_id == current_user.id, Skill.name.like("github_%")
        ).delete()
        for sk in result["skills"]:
            db.add(Skill(name=f"github_{sk}", user_id=current_user.id))
        db.commit()

        # Update cache
        save_profile_cache(db, current_user.id, result)
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing GitHub profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze GitHub profile")

@router.get("/skills")
async def get_github_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    GitHub-derived skills (prefixed github_ in DB; prefix removed in response).
    """
    rows = (
        db.query(Skill)
        .filter(Skill.user_id == current_user.id, Skill.name.like("github_%"))
        .all()
    )
    skills = [r.name.replace("github_", "") for r in rows]
    return {
        "skills": skills,
        "total": len(skills),
        "github_username": current_user.github_username,
    }

@router.get("/all-skills")
async def get_all_user_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Resume + GitHub combined (simple union/intersection).
    """
    rows = db.query(Skill).filter(Skill.user_id == current_user.id).all()
    resume_skills: List[str] = []
    github_skills: List[str] = []

    for s in rows:
        if s.name.startswith("github_"):
            github_skills.append(s.name.replace("github_", ""))
        else:
            resume_skills.append(s.name)

    common = sorted(list(set(resume_skills) & set(github_skills)))
    all_unique = sorted(list(set(resume_skills + github_skills)))

    return {
        "resume_skills": sorted(resume_skills),
        "github_skills": sorted(github_skills),
        "common_skills": common,
        "all_skills": all_unique,
        "total_unique": len(all_unique),
        "stats": {
            "resume_only": len(resume_skills) - len(common),
            "github_only": len(github_skills) - len(common),
            "both": len(common),
        },
    }

@router.delete("/disconnect")
async def disconnect_github(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Disconnect GitHub; remove username, github_* skills, and cached profile.
    """
    current_user.github_username = None
    db.query(Skill).filter(
        Skill.user_id == current_user.id, Skill.name.like("github_%")
    ).delete()
    db.query(TaskStatus).filter(
        TaskStatus.user_id == current_user.id,
        TaskStatus.task_type == "github_profile",
    ).delete()
    db.commit()
    return {"message": "GitHub account disconnected successfully"}
