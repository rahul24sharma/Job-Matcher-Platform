from app.core.cache import cache_get, cache_set, cache_delete
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import User, Job
from app.core.dependencies import get_current_active_user
from app.services.job_matcher import JobMatcher
import logging

router = APIRouter(prefix="/jobs", tags=["jobs"])
logger = logging.getLogger(__name__)

class JobCreate(BaseModel):
    title: str
    company: str
    location: str
    description: str
    required_skills: str  
    url: Optional[str] = None
    remote: bool = False
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None

class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: str
    description: str
    required_skills: str
    url: Optional[str]
    remote: bool
    salary_min: Optional[int]
    salary_max: Optional[int]
    
    class Config:
        from_attributes = True

class JobMatchResponse(BaseModel):
    job_id: int
    title: str
    company: str
    location: str
    remote: bool
    salary_min: Optional[int]
    salary_max: Optional[int]
    match_score: float
    match_reasons: List[str]
    url: Optional[str]

class MatchStatistics(BaseModel):
    total_matches: int
    average_score: float
    top_match_score: float
    match_distribution: Dict[str, int]


def _compute_matches(db: Session, current_user: User) -> List[Dict]:
    """
    Compute (or return cached) matches for the current user.
    Returns a list of JobMatchResponse-like dicts.
    """
    cache_key = f"user_matches:{current_user.id}"
    cached_matches = cache_get(cache_key)
    if cached_matches:
        logger.info(f"Returning cached matches for user {current_user.id}")
        return cached_matches[:20]

    logger.info(f"Calculating new matches for user {current_user.id}")
    matcher = JobMatcher(db)

    matches = matcher.match_jobs_for_user(current_user.id)

    if not matches:
        from app.db.models import Skill
        user_skills = db.query(Skill).filter(Skill.user_id == current_user.id).count()
        if user_skills == 0:
            raise HTTPException(
                status_code=400,
                detail="No skills found. Please upload a resume or connect GitHub first."
            )
        job_count = db.query(Job).count()
        if job_count == 0:
            raise HTTPException(
                status_code=404,
                detail="No jobs available in the database. Please add some jobs first."
            )
        return []

    success = cache_set(cache_key, matches, ttl=21600)  
    logger.info(f"[CACHE] Saving matches for user {current_user.id}: {'SUCCESS' if success else 'FAILED'}")

    return matches[:20]



@router.get("/match", response_model=List[JobMatchResponse])
async def get_fresh_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Recompute (or return cached) matches for current user.
    GET so the frontend doesn't need a POST.
    """
    try:
        return _compute_matches(db, current_user)
    except Exception as e:
        logger.error(f"Error matching jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error matching jobs: {str(e)}")


@router.get("/matches", response_model=List[JobMatchResponse])
async def get_my_matches(
    limit: int = 20,
    min_score: float = 0.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get saved job matches for current user (from Match table).
    """
    from app.db.models import Match
    
    matches = db.query(Match, Job).join(
        Job, Match.job_id == Job.id
    ).filter(
        Match.user_id == current_user.id,
        Match.score >= min_score
    ).order_by(
        Match.score.desc()
    ).limit(limit).all()
    
    results = []
    for match, job in matches:
        reasons = []
        if match.score >= 80:
            reasons.append("Excellent skill match")
        elif match.score >= 60:
            reasons.append("Strong skill match")
        elif match.score >= 40:
            reasons.append("Good skill match")
        else:
            reasons.append("Partial skill match")
        
        results.append({
            "job_id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "remote": job.remote,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "match_score": match.score,
            "match_reasons": reasons,
            "url": job.url
        })
    
    return results


@router.get("/statistics", response_model=MatchStatistics)
async def get_match_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get statistics about job matches
    """
    matcher = JobMatcher(db)
    stats = matcher.get_match_statistics(current_user.id)
    return stats


@router.get("/search/skills")
async def search_jobs_by_skills(
    skills: str, 
    db: Session = Depends(get_db)
):
    """
    Search jobs by required skills
    """
    skill_list = [s.strip() for s in skills.split(',')]
    query = db.query(Job)
    for skill in skill_list:
        query = query.filter(Job.required_skills.ilike(f"%{skill}%"))
    jobs = query.all()
    
    return {
        "search_skills": skill_list,
        "jobs_found": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "required_skills": job.required_skills
            }
            for job in jobs[:10]
        ]
    }


@router.get("/debug/user-skills")
async def debug_user_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Debug endpoint to see user's skills
    """
    from app.db.models import Skill
    
    skills = db.query(Skill).filter(Skill.user_id == current_user.id).all()
    
    resume_skills = []
    github_skills = []
    
    for skill in skills:
        if skill.name.startswith('github_'):
            github_skills.append(skill.name.replace('github_', ''))
        else:
            resume_skills.append(skill.name)
    
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "total_skills": len(skills),
        "resume_skills": resume_skills,
        "github_skills": github_skills,
        "all_skills": sorted(list(set(resume_skills + github_skills)))
    }


@router.get("/", response_model=List[JobResponse])
async def get_all_jobs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get all jobs (no auth required for browsing)
    """
    jobs = db.query(Job).offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific job by ID
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
