from celery import group
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.job_scraper import JobScraperService
from app.tasks.matching_tasks import match_jobs_batch_task
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@celery_app.task(name="scrape_all_jobs")
def scrape_all_jobs_task():
    """
    Main task to scrape jobs from all sources
    """
    logger.info("Starting job scraping task...")
    
    db = SessionLocal()
    try:
        scraper = JobScraperService(db)
        results = scraper.scrape_all_sources()
        
        total_jobs = sum([
            results.get("remotive", 0),
            results.get("adzuna", 0),
            results.get("theirstack", 0)
        ])
        
        logger.info(f"Job scraping completed. Total new jobs: {total_jobs}")
        
        # If new jobs were added, trigger matching for all users
        if total_jobs > 0:
            logger.info("New jobs found, triggering batch matching...")
            match_jobs_batch_task.delay()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "results": results,
            "total_new_jobs": total_jobs
        }
        
    except Exception as e:
        logger.error(f"Error in job scraping task: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()

@celery_app.task(name="cleanup_expired_jobs")
def cleanup_expired_jobs_task():
    """
    Remove jobs that have expired
    """
    db = SessionLocal()
    try:
        from app.db.models import Job
        
        # Delete jobs older than 60 days or past expiration
        cutoff_date = datetime.utcnow() - timedelta(days=60)
        
        expired_count = db.query(Job).filter(
            (Job.expires_at < datetime.utcnow()) | 
            (Job.created_at < cutoff_date)
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {expired_count} expired jobs")
        
        return {
            "status": "success",
            "expired_jobs_removed": expired_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up jobs: {e}")
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="scrape_specific_source")
def scrape_specific_source_task(source: str):
    """
    Scrape jobs from a specific source
    """
    db = SessionLocal()
    try:
        scraper = JobScraperService(db)
        
        if source == "remotive":
            count = scraper.scrape_remotive_jobs()
        elif source == "adzuna":
            count = scraper.scrape_adzuna_jobs()
        elif source == "theirstack":
            count = scraper.scrape_theirstack_jobs()
        else:
            raise ValueError(f"Unknown source: {source}")
        
        logger.info(f"Scraped {count} jobs from {source}")
        
        return {
            "status": "success",
            "source": source,
            "jobs_added": count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error scraping {source}: {e}")
        return {
            "status": "error",
            "source": source,
            "error": str(e)
        }
    finally:
        db.close()

# Update celery beat schedule
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Scrape jobs every 6 hours
    'scrape-all-jobs': {
        'task': 'scrape_all_jobs',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    
    # Update GitHub profiles daily at 2 AM
    'update-github-profiles': {
        'task': 'update_all_github_profiles',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # Run batch matching twice daily
    'batch-job-matching': {
        'task': 'match_jobs_batch',
        'schedule': crontab(hour='8,20', minute=0),  # 8 AM and 8 PM
    },
    
    # Cleanup expired jobs weekly
    'cleanup-expired-jobs': {
        'task': 'cleanup_expired_jobs',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM
    },
    
    # Refresh stale matches every 3 days
    'refresh-stale-matches': {
        'task': 'refresh_stale_matches',
        'schedule': crontab(hour=4, minute=0, day_of_month='*/3'),
    },
}