import re
import fitz  # PyMuPDF
import spacy
from sqlalchemy.orm import Session
from app.db.models import SkillMaster   # ✅ Import your SkillMaster ORM model

nlp = spacy.load("en_core_web_sm")

# ✅ Extract text from PDF
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text


# ✅ Load dynamic skills from DB
def load_dynamic_skills(db: Session) -> set[str]:
    skills = db.query(SkillMaster.name).all()
    return {s[0].lower() for s in skills}


# ✅ Extract skills (basic version using dictionary matching)
def extract_skills(text: str, db: Session) -> list[str]:
    text_lower = text.lower()
    existing_skills = load_dynamic_skills(db)
    found = {skill for skill in existing_skills if re.search(rf"\b{re.escape(skill)}\b", text_lower)}
    return list(found)


# ✅ Save new skills dynamically if they are not already in the DB
def save_new_skills(extracted: set, db: Session):
    existing = load_dynamic_skills(db)
    for skill in extracted:
        if skill not in existing:
            db.add(SkillMaster(name=skill))
    db.commit()
