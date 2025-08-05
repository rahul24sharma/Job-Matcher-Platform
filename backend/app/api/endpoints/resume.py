from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, Skill
from app.core.dependencies import get_current_active_user  # ADD THIS
from app.services.resume_parser import extract_text_from_pdf
from app.services.skill_extractor import extract_skills
import shutil
import os

router = APIRouter(prefix="/resume", tags=["resume"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)  # ADD THIS
):
    # Now you have the authenticated user, no need for email parameter
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Extract text & skills
    text = extract_text_from_pdf(file_path)
    skills = extract_skills(text, db)
    
    # Update user's resume path
    current_user.resume_path = file_path
    db.commit()
    
    # Clear existing skills and add new ones
    db.query(Skill).filter(Skill.user_id == current_user.id).delete()
    
    for s in skills:
        skill = Skill(name=s, user_id=current_user.id)
        db.add(skill)
    
    db.commit()
    
    return {
        "message": "Resume uploaded & parsed successfully",
        "skills": skills,
        "user": current_user.email
    }