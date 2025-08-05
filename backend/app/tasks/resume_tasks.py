from celery import Task
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import User, Skill, TaskStatus
# from app.services.resume_parser import ResumeParser
from app.services import resume_parser
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

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

@celery_app.task(base=CallbackTask, bind=True, name="process_resume")
def process_resume_task(self, user_id: int, file_content: bytes, filename: str):
    """
    Process resume in background
    
    Args:
        self: Task instance (for progress updates)
        user_id: User ID who uploaded the resume
        file_content: Resume file content as bytes
        filename: Original filename
        
    Returns:
        dict: Results including skills extracted and file info
    """
    logger.info(f"Starting resume processing for user {user_id}, file: {filename}")
    
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
                task_type="resume_processing",
                status="processing"
            )
            db.add(task_status)
        else:
            task_status.status = "processing"
        
        db.commit()
        
        # Update progress: Starting
        self.update_state(
            state="PROCESSING", 
            meta={"progress": 10, "message": "Starting resume parsing..."}
        )
        
        # Initialize resume parser
        text = resume_parser.extract_text_from_pdf(file_path)   # or convert bytes to temp file first
        skills = resume_parser.extract_skills(text, db)
        extracted_data = {
            "text": text,
            "skills": skills,
            "filename": filename
        }

        
        # Update progress: Parsing
        self.update_state(
            state="PROCESSING", 
            meta={"progress": 25, "message": "Extracting content from resume..."}
        )
        
        # Parse resume
        try:
            extracted_data = parser.parse_resume(file_content, filename)
        except Exception as e:
            logger.error(f"Resume parsing failed: {str(e)}")
            raise Exception(f"Failed to parse resume: {str(e)}")
        
        # Update progress: Processing skills
        self.update_state(
            state="PROCESSING", 
            meta={"progress": 50, "message": "Processing extracted skills..."}
        )
        
        # Clear existing resume skills for this user
        deleted_count = db.query(Skill).filter(
            Skill.user_id == user_id,
            Skill.source == "resume"
        ).delete()
        logger.info(f"Deleted {deleted_count} existing resume skills for user {user_id}")
        
        # Update progress: Saving skills
        self.update_state(
            state="PROCESSING", 
            meta={"progress": 75, "message": "Saving skills to database..."}
        )
        
        # Add new skills
        skills_added = 0
        skills_list = []
        
        for skill_name in extracted_data.get("skills", []):
            # Clean and normalize skill name
            skill_name_clean = skill_name.strip().lower()
            
            # Skip empty skills
            if not skill_name_clean:
                continue
                
            # Check if skill already exists for user (from other sources)
            existing_skill = db.query(Skill).filter(
                Skill.user_id == user_id,
                Skill.name == skill_name_clean,
                Skill.source != "resume"
            ).first()
            
            if not existing_skill:
                skill = Skill(
                    user_id=user_id,
                    name=skill_name_clean,
                    source="resume",
                    proficiency="intermediate"  # Default proficiency
                )
                db.add(skill)
                skills_added += 1
                skills_list.append(skill_name_clean)
        
        # Commit all skills
        db.commit()
        
        # Update progress: Complete
        self.update_state(
            state="PROCESSING", 
            meta={"progress": 100, "message": "Resume processing completed!"}
        )
        
        # Prepare result
        result = {
            "success": True,
            "skills_extracted": skills_added,
            "skills_list": skills_list[:10],  # First 10 skills for preview
            "total_skills_found": len(extracted_data.get("skills", [])),
            "text_length": len(extracted_data.get("text", "")),
            "filename": filename,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        # Also update user's resume_text if extracted
        if extracted_data.get("text"):
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.resume_text = extracted_data["text"][:5000]  # Store first 5000 chars
                db.commit()
        
        logger.info(f"Resume processed successfully for user {user_id}: {skills_added} skills added")
        return result
        
    except Exception as e:
        logger.error(f"Error processing resume for user {user_id}: {str(e)}")
        # Re-raise to trigger on_failure callback
        raise
        
    finally:
        db.close()


@celery_app.task(name="cleanup_old_tasks")
def cleanup_old_tasks():
    """
    Periodic task to clean up old task records
    (Run daily via Celery Beat)
    """
    db = SessionLocal()
    try:
        # Delete completed/failed tasks older than 7 days
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        deleted_count = db.query(TaskStatus).filter(
            TaskStatus.completed_at < cutoff_date,
            TaskStatus.status.in_(["completed", "failed"])
        ).delete()
        
        db.commit()
        logger.info(f"Cleaned up {deleted_count} old task records")
        
        return {"deleted_tasks": deleted_count}
        
    except Exception as e:
        logger.error(f"Error cleaning up tasks: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()