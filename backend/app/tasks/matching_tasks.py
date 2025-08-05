from celery import group
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import User, Job, Match
from app.services.job_matcher import JobMatcher
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


@celery_app.task(name="match_jobs_batch")
def match_jobs_batch_task(user_ids: Optional[List[int]] = None):
    """
    Run job matching for multiple users (batch processing)
    Used by Airflow for scheduled matching
    
    Args:
        user_ids: Optional list of user IDs. If None, process all active users
        
    Returns:
        dict: Summary of matching results
    """
    logger.info(f"Starting batch job matching for users: {user_ids or 'all'}")
    
    db = SessionLocal()
    try:
        # Get users to process
        query = db.query(User).filter(User.is_active == True)
        
        if user_ids:
            query = query.filter(User.id.in_(user_ids))
        
        users = query.all()
        logger.info(f"Found {len(users)} users to process")
        
        # Check if there are jobs available
        job_count = db.query(Job).count()
        if job_count == 0:
            logger.warning("No jobs available for matching")
            return {
                "status": "no_jobs",
                "users_processed": 0,
                "message": "No jobs available in database"
            }
        
        # Initialize matcher
        matcher = JobMatcher(db)
        
        # Process each user
        results = []
        successful_matches = 0
        failed_matches = 0
        
        for user in users:
            try:
                # Skip users without skills
                from app.db.models import Skill
                user_skills_count = db.query(Skill).filter(
                    Skill.user_id == user.id
                ).count()
                
                if user_skills_count == 0:
                    logger.info(f"Skipping user {user.id} - no skills")
                    results.append({
                        "user_id": user.id,
                        "status": "skipped",
                        "reason": "no_skills"
                    })
                    continue
                
                # Run matching
                matches = matcher.match_jobs_for_user(user.id)
                
                results.append({
                    "user_id": user.id,
                    "status": "success",
                    "matches_found": len(matches),
                    "top_score": matches[0]["match_score"] if matches else 0,
                    "top_match": matches[0]["title"] if matches else None
                })
                successful_matches += 1
                
                logger.info(f"Matched {len(matches)} jobs for user {user.id}")
                
            except Exception as e:
                logger.error(f"Error matching for user {user.id}: {str(e)}")
                results.append({
                    "user_id": user.id,
                    "status": "failed",
                    "error": str(e)
                })
                failed_matches += 1
        
        # Summary
        summary = {
            "status": "completed",
            "total_users": len(users),
            "successful_matches": successful_matches,
            "failed_matches": failed_matches,
            "users_skipped": len(users) - successful_matches - failed_matches,
            "job_count": job_count,
            "processed_at": datetime.utcnow().isoformat(),
            "results": results
        }
        
        logger.info(f"Batch matching completed: {successful_matches} successful, {failed_matches} failed")
        return summary
        
    except Exception as e:
        logger.error(f"Error in batch job matching: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "processed_at": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


@celery_app.task(name="match_single_user", bind=True)
def match_single_user_task(self, user_id: int):
    """
    Match jobs for a single user (real-time)
    Shows progress updates
    
    Args:
        user_id: User ID to match jobs for
        
    Returns:
        dict: Matching results with top matches
    """
    logger.info(f"Starting job matching for user {user_id}")
    
    db = SessionLocal()
    try:
        # Update progress: Starting
        self.update_state(
            state="PROCESSING",
            meta={"progress": 10, "message": "Initializing job matching..."}
        )
        
        # Verify user exists and has skills
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        from app.db.models import Skill
        user_skills_count = db.query(Skill).filter(
            Skill.user_id == user_id
        ).count()
        
        if user_skills_count == 0:
            return {
                "user_id": user_id,
                "status": "no_skills",
                "matches_found": 0,
                "message": "User has no skills. Please upload resume or connect GitHub."
            }
        
        # Update progress: Loading jobs
        self.update_state(
            state="PROCESSING",
            meta={"progress": 30, "message": f"Analyzing {user_skills_count} skills..."}
        )
        
        # Check available jobs
        job_count = db.query(Job).count()
        if job_count == 0:
            return {
                "user_id": user_id,
                "status": "no_jobs",
                "matches_found": 0,
                "message": "No jobs available in database"
            }
        
        # Update progress: Matching
        self.update_state(
            state="PROCESSING",
            meta={"progress": 50, "message": f"Matching against {job_count} jobs..."}
        )
        
        # Run matching
        matcher = JobMatcher(db)
        matches = matcher.match_jobs_for_user(user_id)
        
        # Update progress: Saving results
        self.update_state(
            state="PROCESSING",
            meta={"progress": 80, "message": "Saving match results..."}
        )
        
        # Get match statistics
        stats = matcher.get_match_statistics(user_id)
        
        # Update progress: Complete
        self.update_state(
            state="PROCESSING",
            meta={"progress": 100, "message": "Matching completed!"}
        )
        
        # Prepare top matches for response
        top_matches = []
        for match in matches[:5]:  # Top 5 matches
            top_matches.append({
                "job_id": match["job_id"],
                "title": match["title"],
                "company": match["company"],
                "match_score": match["match_score"],
                "match_reasons": match["match_reasons"][:2]  # First 2 reasons
            })
        
        result = {
            "user_id": user_id,
            "status": "success",
            "matches_found": len(matches),
            "top_matches": top_matches,
            "statistics": stats,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Job matching completed for user {user_id}: {len(matches)} matches")
        return result
        
    except Exception as e:
        logger.error(f"Error matching jobs for user {user_id}: {str(e)}")
        raise
        
    finally:
        db.close()


@celery_app.task(name="refresh_stale_matches")
def refresh_stale_matches_task(days_old: int = 7):
    """
    Refresh matches for users whose matches are older than specified days
    
    Args:
        days_old: Number of days to consider matches as stale
        
    Returns:
        dict: Summary of refresh operation
    """
    db = SessionLocal()
    try:
        from sqlalchemy import func
        
        # Find users with stale matches
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Get users whose latest match is older than cutoff
        subquery = db.query(
            Match.user_id,
            func.max(Match.created_at).label('latest_match')
        ).group_by(Match.user_id).subquery()
        
        stale_users = db.query(User.id).join(
            subquery, User.id == subquery.c.user_id
        ).filter(
            subquery.c.latest_match < cutoff_date
        ).all()
        
        user_ids = [user.id for user in stale_users]
        
        if not user_ids:
            return {
                "status": "no_stale_matches",
                "message": f"No users with matches older than {days_old} days"
            }
        
        # Schedule batch matching for these users
        task = match_jobs_batch_task.delay(user_ids)
        
        return {
            "status": "scheduled",
            "users_scheduled": len(user_ids),
            "task_id": task.id,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    finally:
        db.close()


@celery_app.task(name="match_new_jobs")
def match_new_jobs_task(job_ids: List[int]):
    """
    When new jobs are added, match them against all users
    (Called after job scraping)
    
    Args:
        job_ids: List of new job IDs to match
        
    Returns:
        dict: Summary of matching operation
    """
    db = SessionLocal()
    try:
        # Get all active users with skills
        from app.db.models import Skill
        
        users_with_skills = db.query(User.id).join(
            Skill, User.id == Skill.user_id
        ).filter(
            User.is_active == True
        ).distinct().all()
        
        user_ids = [user.id for user in users_with_skills]
        
        if not user_ids:
            return {
                "status": "no_users",
                "message": "No active users with skills found"
            }
        
        # Run batch matching for all users
        # This will include the new jobs in matching
        task = match_jobs_batch_task.delay(user_ids)
        
        return {
            "status": "scheduled",
            "new_jobs_count": len(job_ids),
            "users_to_match": len(user_ids),
            "task_id": task.id
        }
        
    finally:
        db.close()
