# app/api/endpoints/job_scraping.py

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import get_current_active_user
from app.services.job_scraper import JobScraperService
from app.tasks.job_scraping_tasks import scrape_all_jobs_task, scrape_specific_source_task
from app.db.models import Job, User
from datetime import datetime
from sqlalchemy import func
import requests
import logging

router = APIRouter(prefix="/scraping", tags=["job-scraping"])
logger = logging.getLogger(__name__)

@router.post("/scrape-now")
async def trigger_job_scraping(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger job scraping (admin only in production)
    """
    # Start async task
    task = scrape_all_jobs_task.delay()
    
    return {
        "message": "Job scraping started",
        "task_id": task.id,
        "status": "processing"
    }

@router.post("/scrape-source/{source}")
async def scrape_specific_source(
    source: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Scrape jobs from a specific source
    """
    if source not in ["remotive", "adzuna", "theirstack", "arbeitnow"]:
        raise HTTPException(status_code=400, detail="Invalid source")
    
    task = scrape_specific_source_task.delay(source)
    
    return {
        "message": f"Scraping {source} started",
        "task_id": task.id
    }

@router.get("/stats")
async def get_scraping_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get job scraping statistics
    """
    # Count jobs by source
    stats = db.query(
        Job.source,
        func.count(Job.id).label('count'),
        func.max(Job.created_at).label('latest')
    ).group_by(Job.source).all()
    
    # Count jobs by date
    today = datetime.utcnow().date()
    today_jobs = db.query(Job).filter(
        func.date(Job.created_at) == today
    ).count()
    
    # Active jobs
    active_jobs = db.query(Job).filter(
        Job.is_active == True,
        (Job.expires_at > datetime.utcnow()) | (Job.expires_at == None)
    ).count()
    
    return {
        "total_active_jobs": active_jobs,
        "jobs_added_today": today_jobs,
        "by_source": [
            {
                "source": stat.source,
                "count": stat.count,
                "latest_job": stat.latest.isoformat() if stat.latest else None
            }
            for stat in stats
        ],
        "last_scrape": None  # You can track this separately
    }

@router.get("/preview/{source}")
async def preview_source_jobs(
    source: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Preview what jobs would be scraped from a source (without saving)
    """
    scraper = JobScraperService(db)
    
    try:
        if source == "remotive":
            # Just fetch without saving
            url = "https://remotive.io/api/remote-jobs"
            response = requests.get(url, params={"limit": 5})
            response.raise_for_status()
            jobs = response.json().get("jobs", [])
            
            return {
                "source": source,
                "preview_count": len(jobs),
                "jobs": [
                    {
                        "title": job.get("title"),
                        "company": job.get("company_name"),
                        "url": job.get("url"),
                        "location": job.get("candidate_required_location", "Remote")
                    }
                    for job in jobs[:5]
                ]
            }
        elif source == "theirstack":
            url = "https://api.theirstack.com/v1/jobs"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            jobs = response.json()[:5]

        elif source == "arbeitnow":  # ← ADD THIS NEW BLOCK
            url = "https://www.arbeitnow.com/api/job-board-api"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            jobs = data.get("data", [])[:5]
            
            return {
                "source": source,
                "preview_count": len(jobs),
                "jobs": [
                    {
                        "title": job.get("title"),
                        "company": job.get("company"),
                        "location": job.get("location", "Unknown")
                    }
                    for job in jobs
                ]
            }
        else:
            raise HTTPException(status_code=400, detail=f"Preview not available for source: {source}")
            
    except requests.RequestException as e:
        logger.error(f"Error previewing {source}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs from {source}")
    except Exception as e:
        logger.error(f"Unexpected error previewing {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-scraper")
async def test_scraper_direct(
    source: str = "remotive",
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Test job scraping directly (synchronous, for debugging)
    """
    scraper = JobScraperService(db)
    
    try:
        if source == "remotive":
            count = scraper.scrape_remotive_jobs(limit=limit)
        elif source == "theirstack":
            count = scraper.scrape_theirstack_jobs(limit=limit)
        elif source == "adzuna":
            count = scraper.scrape_adzuna_jobs(limit=limit)
        elif source == "arbeitnow":  # ← ADD THIS NEW BLOCK
            count = scraper.scrape_arbeitnow_jobs(limit=limit)

        else:
            raise HTTPException(status_code=400, detail="Invalid source")
        
        return {
            "message": f"Successfully scraped {count} jobs from {source}",
            "source": source,
            "jobs_added": count
        }
        
    except Exception as e:
        logger.error(f"Error in test scraper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup-duplicates")
async def cleanup_duplicate_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Remove duplicate jobs based on external_id
    """
    # Find and remove duplicates
    from sqlalchemy import text
    
    # Keep the oldest job for each external_id
    result = db.execute(text("""
        DELETE FROM jobs 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM jobs 
            GROUP BY external_id
        )
    """))
    
    db.commit()
    
    return {
        "message": "Duplicate jobs cleaned up",
        "deleted_count": result.rowcount
    }