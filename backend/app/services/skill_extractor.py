import re
import spacy
from sqlalchemy.orm import Session
from app.db.models import SkillMaster

nlp = spacy.load("en_core_web_sm")

def load_dynamic_skills(db: Session) -> set[str]:
    skills = db.query(SkillMaster.name).all()
    return {s[0].lower() for s in skills}

def extract_skills(text: str, db: Session) -> list[str]:
    text_lower = text.lower()
    doc = nlp(text)
    dynamic_skills = load_dynamic_skills(db)
    extracted = set()

    # ✅ 1. Match skills from DB
    for skill in dynamic_skills:
        if re.search(rf"\b{re.escape(skill)}\b", text_lower):
            extracted.add(skill)

    # ✅ 2. Use NER to detect unknown technologies
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT"]:  # spaCy often tags tech names here
            candidate = ent.text.lower()
            if candidate not in dynamic_skills:
                extracted.add(candidate)  # treat as a new potential skill

    # ✅ 3. Include noun chunks (some frameworks might be missed by NER)
    for chunk in doc.noun_chunks:
        token = chunk.text.lower()
        if len(token) > 2 and token not in extracted and re.match(r"^[a-z0-9\-\.\+]+$", token):
            extracted.add(token)

    return list(extracted)

def save_new_skills(extracted: set, db: Session):
    existing = load_dynamic_skills(db)
    for skill in extracted:
        if skill not in existing:
            db.add(SkillMaster(name=skill))
    db.commit()
