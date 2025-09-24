# app/services/skill_extractor.py
import re
import spacy
from typing import Iterable, List, Set
from sqlalchemy.orm import Session
from app.db.models import SkillMaster

nlp = spacy.load("en_core_web_sm")

ALIASES = {
    "reactjs": "react",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "ci/cd": "ci-cd",
    "cicd": "ci-cd",
    "js": "javascript",
}

def load_dynamic_skills(db: Session) -> set[str]:
    skills = db.query(SkillMaster.name).all()
    return {s[0].lower() for s in skills}

def extract_skills(text: str, db: Session) -> list[str]:
    text_lower = text.lower()
    doc = nlp(text)
    dynamic_skills = load_dynamic_skills(db)
    extracted: Set[str] = set()

    # 1) Exact matches from master
    for skill in dynamic_skills:
        if re.search(rf"\b{re.escape(skill)}\b", text_lower):
            extracted.add(skill)

    # 2) NER candidates
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT"]:
            candidate = ent.text.lower().strip()
            if candidate and candidate not in dynamic_skills:
                extracted.add(candidate)

    # 3) Noun chunks fallback
    for chunk in doc.noun_chunks:
        token = chunk.text.lower().strip()
        if (
            2 < len(token) < 40
            and token not in extracted
            and re.match(r"^[a-z0-9\-\.\+ ]+$", token)
        ):
            extracted.add(token)

    return list(extracted)

def clean_skills(raw: Iterable[str]) -> List[str]:
    """Normalize, alias, dedupe. You can add a whitelist here if you want to be stricter."""
    out: List[str] = []
    seen: Set[str] = set()
    for s in raw:
        if not s:
            continue
        t = re.sub(r"\s+", " ", s.strip().lower())
        t = ALIASES.get(t, t)
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out

def save_new_skills(candidates: Iterable[str], db: Session) -> None:
    """Optionally expand SkillMaster from extracted skills."""
    existing = load_dynamic_skills(db)
    to_add = [SkillMaster(name=s) for s in candidates if s not in existing]
    if to_add:
        db.add_all(to_add)
        db.commit()
