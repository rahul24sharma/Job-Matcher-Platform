from celery import Task
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import User, Skill, TaskStatus
from app.services.github_analyzer import GitHubAnalyzer
import logging
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger(__name__)

# Reuse CallbackTask from resume_tasks or define it here
class CallbackTask(Task):
    """Base task with callbacks for status tracking"""
    def on_success(self, retval, task_id, args, kwargs):
        """Success callback - update task status to completed"""
        db = SessionLocal()
        try:
            task_status = db.query(TaskStatus).filter(
                TaskStatus.task_id == task_id
            ).first()
            if task_status:
                task_status.status = "completed"
                task_status.result = retval
                task_status.completed_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Error updating task success status: {str(e)}")
        finally:
            db.close()
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Failure callback - update task status to failed"""
        db = SessionLocal()
        try:
            task_status = db.query(TaskStatus).filter(
                TaskStatus.task_id == task_id
            ).first()
            if task_status:
                task_status.status = "failed"
                task_status.error = str(exc)
                task_status.completed_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Error updating task failure status: {str(e)}")
        finally:
            db.close()


@celery_app.task(base=CallbackTask, bind=True, name="analyze_github")
def analyze_github_profile_task(self, user_id: int):
    """
    Analyze GitHub profile in background
    
    Args:
        self: Task instance (for progress updates)
        user_id: User ID to analyze
        
    Returns:
        dict: Analysis results including languages and repositories
    """
    logger.info(f"Starting GitHub analysis for user {user_id}")
    
    db = SessionLocal()
    try:
        # Create or update task status
        task_status = db.query(TaskStatus).filter(
            TaskStatus.task_id == self.request.id
        ).first()
        
        if not task_status:
            task_status = TaskStatus(
                task_id=self.request.id,
                user_id=user_id,
                task_type="github_analysis",
                status="processing"
            )
            db.add(task_status)
        else:
            task_status.status = "processing"
        
        db.commit()
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        if not user.github_username:
            raise ValueError(f"User {user_id} has no GitHub username")
        
        # Update progress: Starting
        self.update_state(
            state="PROCESSING", 
            meta={
                "progress": 10,
                "message": f"Fetching GitHub profile for {user.github_username}..."
            }
        )
        
        # Initialize GitHub analyzer
        analyzer = GitHubAnalyzer()
        
        # Update progress: Analyzing
        self.update_state(
            state="PROCESSING", 
            meta={
                "progress": 30,
                "message": "Analyzing repositories..."
            }
        )
        
        # Analyze GitHub profile
        try:
            analysis = analyzer.analyze_user(user.github_username)
        except Exception as e:
            logger.error(f"GitHub analysis failed: {str(e)}")
            raise Exception(f"Failed to analyze GitHub profile: {str(e)}")
        
        # Update progress: Processing languages
        self.update_state(
            state="PROCESSING", 
            meta={
                "progress": 60,
                "message": "Processing programming languages..."
            }
        )
        
        # Clear existing GitHub skills
        deleted_count = db.query(Skill).filter(
            Skill.user_id == user_id,
            Skill.source == "github"
        ).delete()
        logger.info(f"Deleted {deleted_count} existing GitHub skills for user {user_id}")
        
        # Update progress: Saving skills
        self.update_state(
            state="PROCESSING", 
            meta={
                "progress": 80,
                "message": "Saving skills to database..."
            }
        )
        
        # Add language skills based on usage
        skills_added = 0
        skills_list = []
        
        for lang, stats in analysis.get("languages", {}).items():
            # Only add languages with significant usage
            if stats["percentage"] > 5:  # More than 5% of code
                skill_name = f"github_{lang.lower()}"
                proficiency = _calculate_proficiency(stats["percentage"])
                
                skill = Skill(
                    user_id=user_id,
                    name=skill_name,
                    source="github",
                    proficiency=proficiency
                )
                db.add(skill)
                skills_added += 1
                skills_list.append(lang)
        
        # Add framework/library skills based on repo analysis
        for framework in analysis.get("frameworks", []):
            skill = Skill(
                user_id=user_id,
                name=f"github_{framework.lower()}",
                source="github",
                proficiency="intermediate"
            )
            db.add(skill)
            skills_added += 1
            skills_list.append(framework)
        
        # Update user's github_data field
        user.github_data = {
            "username": user.github_username,
            "repos_count": analysis.get("repos_count", 0),
            "total_stars": analysis.get("total_stars", 0),
            "followers": analysis.get("followers", 0),
            "top_languages": analysis.get("top_languages", []),
            "languages": analysis.get("languages", {}),
            "last_updated": datetime.utcnow().isoformat(),
            "profile_url": f"https://github.com/{user.github_username}"
        }
        
        db.commit()
        
        # Update progress: Complete
        self.update_state(
            state="PROCESSING", 
            meta={
                "progress": 100,
                "message": "GitHub analysis completed!"
            }
        )
        
        # Prepare result
        result = {
            "success": True,
            "username": user.github_username,
            "repos_analyzed": analysis.get("repos_count", 0),
            "skills_extracted": skills_added,
            "skills_list": skills_list[:10],  # Top 10 skills
            "top_language": analysis.get("top_languages", ["None"])[0],
            "total_stars": analysis.get("total_stars", 0),
            "processed_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"GitHub analysis completed for user {user_id}: {skills_added} skills added")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing GitHub for user {user_id}: {str(e)}")
        raise
        
    finally:
        db.close()


def _calculate_proficiency(percentage: float) -> str:
    """Calculate proficiency level based on language usage percentage"""
    if percentage >= 50:
        return "expert"
    elif percentage >= 30:
        return "advanced"
    elif percentage >= 15:
        return "intermediate"
    else:
        return "beginner"


@celery_app.task(name="update_all_github_profiles")
def update_all_github_profiles_task():
    """
    Batch update all users' GitHub profiles
    (For Airflow daily updates)
    """
    db = SessionLocal()
    try:
        # Get all users with GitHub usernames
        users = db.query(User).filter(
            User.github_username.isnot(None),
            User.is_active == True
        ).all()
        
        results = []
        for user in users:
            try:
                # Check if recently updated (within 24 hours)
                if user.github_data:
                    last_updated = user.github_data.get("last_updated")
                    if last_updated:
                        last_update_time = datetime.fromisoformat(last_updated)
                        if datetime.utcnow() - last_update_time < timedelta(hours=24):
                            logger.info(f"Skipping user {user.id} - recently updated")
                            continue
                
                # Schedule individual analysis task
                task = analyze_github_profile_task.delay(user.id)
                results.append({
                    "user_id": user.id,
                    "task_id": task.id,
                    "github_username": user.github_username
                })
                
            except Exception as e:
                logger.error(f"Error scheduling GitHub update for user {user.id}: {str(e)}")
                results.append({
                    "user_id": user.id,
                    "error": str(e)
                })
        
        return {
            "users_scheduled": len(results),
            "results": results
        }
        
    finally:
        db.close()