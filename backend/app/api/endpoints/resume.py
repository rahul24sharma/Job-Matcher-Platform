from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, Skill
from app.core.dependencies import get_current_active_user
from app.services.resume_parser import extract_text_from_pdf
from app.services.skill_extractor import extract_skills, clean_skills, save_new_skills
import shutil
import os

router = APIRouter(prefix="/resume", tags=["resume"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extract_text_from_pdf(file_path)
    raw_skills = extract_skills(text, db)
    skills = clean_skills(raw_skills)  

    current_user.resume_path = file_path
    db.commit()

    db.query(Skill).filter(Skill.user_id == current_user.id).delete()
    db.add_all([Skill(name=s, user_id=current_user.id) for s in skills])
    db.commit()


    return {
        "message": "Resume uploaded & parsed successfully",
        "skills": skills,
        "user": current_user.email,
    }

@router.post("/reparse")
def reparse_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.resume_path or not os.path.exists(current_user.resume_path):
        raise HTTPException(status_code=404, detail="No resume on file")
    text = extract_text_from_pdf(current_user.resume_path)
    skills = clean_skills(extract_skills(text, db))
    db.query(Skill).filter(Skill.user_id == current_user.id).delete()
    db.add_all([Skill(name=s, user_id=current_user.id) for s in skills])
    db.commit()
    return {"message": "Reparsed successfully", "skills": skills}
