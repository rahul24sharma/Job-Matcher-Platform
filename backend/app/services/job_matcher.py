# app/services/job_matcher.py

from typing import List, Dict, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import or_
import re
from datetime import datetime
import logging

from app.db.models import User, Skill, Job, Match, SkillMaster

logger = logging.getLogger(__name__)

# --- NEW: simple aliases/synonyms map (extend as needed) ---
ALIASES = {
    "react.js": "react",
    "reactjs": "react",
    "nodejs": "node.js",
    "node js": "node.js",
    "js": "javascript",
    "ts": "typescript",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "k8s": "kubernetes",
    "ci cd": "ci/cd",
    "dotnet": ".net",
    "c sharp": "c#",
    "golang": "go",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "vue.js": "vue",
    "vuejs": "vue",
    "angular.js": "angular",
    "angularjs": "angular",
}

BULLETS = r"\u2022|\u2023|\u25E6|\u2043|\u2219|•|·|●"

def _norm_token(s: str) -> str:
    s = (s or "").lower().strip()
    # normalize bullets & connectors
    s = re.sub(BULLETS, " ", s)
    s = s.replace("&", " and ")
    # keep letters, digits, + # . - / and space
    s = re.sub(r"[^a-z0-9\+\#\.\-/ ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # apply alias map
    return ALIASES.get(s, s)

def _tokenize_skills(raw: str) -> Set[str]:
    """Split on common delimiters and bullets; normalize each token."""
    if not raw:
        return set()
    parts = re.split(rf"[,\|;/\n\t]+|{BULLETS}", raw)
    return { _norm_token(p) for p in parts if _norm_token(p) }

class JobMatcher:
    def __init__(self, db: Session):
        self.db = db
        # cache SkillMaster names for fallback scanning (optional)
        try:
            self._skillmaster = { _norm_token(n) for (n,) in db.query(SkillMaster.name).all() } or set()
        except:
            logger.warning("SkillMaster table not available, using empty set")
            self._skillmaster = set()

    def match_jobs_for_user(self, user_id: int) -> List[Dict]:
        """Match jobs for a user based on their skills."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            return []

        user_skills = self._get_user_skills(user_id)
        if not user_skills:
            logger.info(f"User {user_id} has no skills")
            return []

        jobs = self.db.query(Job).all()
        if not jobs:
            logger.info("No jobs in database")
            return []

        matched_jobs = []
        for job in jobs:
            match_score, match_reasons = self._calculate_match_score(user_skills, job, user)
            if match_score > 0:
                matched_jobs.append({
                    "job_id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "remote": job.remote,
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "description": job.description,
                    "required_skills": job.required_skills,
                    "url": job.url,
                    "match_score": match_score,
                    "match_reasons": match_reasons,
                    "created_at": job.created_at
                })

        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        self._save_matches(user_id, matched_jobs[:50])
        return matched_jobs

    def _get_user_skills(self, user_id: int) -> Set[str]:
        """Resume + GitHub skills, normalized and alias-adjusted."""
        rows = self.db.query(Skill.name).filter(Skill.user_id == user_id).all()
        user_skills = {
            _norm_token(name.replace("github_", "")) for (name,) in rows if name
        }
        # remove empties
        user_skills = {s for s in user_skills if s}
        logger.info(f"User {user_id} has {len(user_skills)} unique skills (normalized)")
        return user_skills

    def _get_job_skills(self, job: Job) -> Set[str]:
        """Extract job skills with robust tokenization + fallback."""
        if job.required_skills:
            skills = _tokenize_skills(job.required_skills)
        else:
            skills = set()
        
        # fallback: scan description against SkillMaster terms
        if not skills and job.description:
            text = _norm_token(job.description)
            skills = { sm for sm in self._skillmaster if re.search(rf"\b{re.escape(sm)}\b", text) }
        
        return skills

    def _ordered_job_skills(self, job: Job) -> List[str]:
        """
        Extract job skills in order of appearance/importance.
        Skills that appear first in the requirements are considered more important.
        """
        ordered = []
        seen = set()
        
        # First try to extract from required_skills field
        if job.required_skills:
            # Split by common delimiters while preserving order
            parts = re.split(rf"[,\|;/\n\t]+|{BULLETS}", job.required_skills)
            
            for part in parts:
                skill = _norm_token(part)
                if skill and skill not in seen:
                    ordered.append(skill)
                    seen.add(skill)
        
        # If we didn't get enough skills, try extracting from description
        if len(ordered) < 3 and job.description:
            text = job.description.lower()
            
            # Look for skills section in description
            skills_section = ""
            markers = ["skills:", "requirements:", "required:", "qualifications:", 
                      "must have:", "technical skills:", "what you'll need:"]
            
            for marker in markers:
                if marker in text:
                    idx = text.index(marker)
                    # Get next 500 chars after the marker
                    skills_section = text[idx:idx+500]
                    break
            
            if skills_section:
                # Extract skills from the skills section
                parts = re.split(rf"[,\|;/\n\t]+|{BULLETS}", skills_section)
                for part in parts:
                    skill = _norm_token(part)
                    # Filter out common non-skill words
                    if (skill and skill not in seen and 
                        len(skill) > 1 and 
                        skill not in ["and", "or", "with", "using", "years", "experience"]):
                        ordered.append(skill)
                        seen.add(skill)
                        if len(ordered) >= 15:  # Reasonable limit
                            break
            
            # Last resort: check against known skills from SkillMaster
            if len(ordered) < 5 and self._skillmaster:
                text_norm = _norm_token(job.description)
                for skill in self._skillmaster:
                    if skill not in seen and re.search(rf"\b{re.escape(skill)}\b", text_norm):
                        ordered.append(skill)
                        seen.add(skill)
                        if len(ordered) >= 10:
                            break
        
        return ordered

    def _calculate_match_score(self, user_skills: Set[str], job: Job, user: User) -> Tuple[float, List[str]]:
        """Calculate match score between user skills and job requirements."""
        reasons: List[str] = []

        # Get job skills
        job_skills = self._get_job_skills(job)
        if not job_skills:
            return 0.0, ["No skills specified for this job"]

        matched = user_skills & job_skills
        missing = job_skills - user_skills

        # --- 1) Base: strict overlap (60%) ---
        base_ratio = len(matched) / max(len(job_skills), 1)
        score = base_ratio * 60.0
        if matched:
            matched_list = sorted(list(matched))[:5]
            reasons.append(f"Matching skills: {', '.join(matched_list)}")

        # --- 2) Core skills coverage (bonus + penalty) ---
        ordered = self._ordered_job_skills(job)
        # Take first 5 as "core" skills
        core = ordered[:5] if ordered else list(job_skills)[:5]
        core_set = set(core)
        core_matched = core_set & matched
        core_missing = core_set - matched

        # Bonus up to +18 for core coverage, penalty up to -15 for missing core
        if core:
            core_bonus = (len(core_matched) / len(core)) * 18.0
            core_penalty = (len(core_missing) / len(core)) * 15.0
            score += core_bonus
            
            if core_missing:
                score -= core_penalty
                missing_list = sorted(list(core_missing))[:4]
                reasons.append(f"Missing core skills: {', '.join(missing_list)}")
            
            if core_matched:
                matched_core_list = sorted(list(core_matched))[:4]
                reasons.append(f"Core skills matched: {', '.join(matched_core_list)}")

        # --- 3) Related skills (cap at 6) ---
        related = self._find_related_skills(user_skills, missing)
        if related:
            add = min(6.0, len(related) * 1.5)
            score += add
            related_list = sorted(list(related))[:3]
            reasons.append(f"Related skills: {', '.join(related_list)}")

        # --- 4) Location (≤4) ---
        if job.location:
            jl = job.location.lower()
            user_location = getattr(user, 'location', '').lower() if user else ''
            
            if job.remote or any(tok in jl for tok in ["remote", "anywhere", "worldwide"]):
                score += 4.0
                reasons.append("Remote position")
            elif user_location and (
                user_location in jl or 
                jl in user_location or
                any(city in jl for city in user_location.split(','))
            ):
                score += 4.0
                reasons.append("Location match")

        # --- 5) Experience level match (≤4) ---
        title = (job.title or "").lower()
        desc = (job.description or "").lower()
        user_skill_count = len(user_skills)
        
        # Senior level
        if any(k in title or k in desc[:200] for k in ["senior", "lead", "principal", "staff", "architect"]):
            if user_skill_count >= 15:
                score += 4.0
                reasons.append("Experience level match (Senior)")
            else:
                score -= 2.0  # Penalty for under-qualified
        # Junior level
        elif any(k in title or k in desc[:200] for k in ["junior", "entry", "intern", "graduate", "trainee"]):
            if user_skill_count <= 10:
                score += 4.0
                reasons.append("Experience level match (Entry/Junior)")
        # Mid level (default)
        else:
            if 8 <= user_skill_count <= 20:
                score += 4.0
                reasons.append("Experience level match (Mid-level)")

        # --- 6) Coverage bonus (≤4) ---
        if base_ratio >= 0.85:
            score += 4.0
            reasons.append(f"Excellent skill coverage ({int(base_ratio*100)}%)")
        elif base_ratio >= 0.70:
            score += 2.0
            reasons.append(f"Good skill coverage ({int(base_ratio*100)}%)")
        elif base_ratio >= 0.50:
            score += 1.0
            reasons.append(f"Moderate skill coverage ({int(base_ratio*100)}%)")

        # --- 7) Penalty for too many missing skills ---
        if len(missing) > 5:
            penalty = min(10.0, (len(missing) - 5) * 1.5)
            score -= penalty
            reasons.append(f"Many missing skills (-{penalty:.1f} points)")

        # Clamp 0..100 and round
        score = max(0.0, min(100.0, round(score, 2)))
        
        # Add summary
        if score >= 80:
            reasons.insert(0, "⭐ Excellent match!")
        elif score >= 60:
            reasons.insert(0, "✓ Good match")
        elif score >= 40:
            reasons.insert(0, "○ Moderate match")
        
        return score, reasons

    def _find_related_skills(self, user_skills: Set[str], required_skills: Set[str]) -> Set[str]:
        """Find related skills between user skills and required skills."""
        related_matches = set()
        
        # Expanded relations map
        relations = {
            "python": ["django", "flask", "fastapi", "pandas", "numpy", "scikit-learn", "pytorch"],
            "javascript": ["react", "angular", "vue", "node.js", "express", "typescript", "next.js", "jquery"],
            "typescript": ["javascript", "react", "angular", "node.js"],
            "java": ["spring", "spring boot", "hibernate", "maven", "gradle"],
            "c#": [".net", "asp.net", "entity framework", "xamarin"],
            ".net": ["c#", "asp.net", "entity framework"],
            "php": ["laravel", "symfony", "wordpress", "drupal"],
            "ruby": ["rails", "ruby on rails", "sinatra"],
            "go": ["golang", "gin", "echo"],
            "rust": ["actix", "rocket"],
            "sql": ["postgresql", "mysql", "sqlite", "oracle", "sql server"],
            "postgresql": ["sql", "postgres"],
            "mysql": ["sql", "mariadb"],
            "nosql": ["mongodb", "redis", "cassandra", "dynamodb", "couchdb"],
            "mongodb": ["nosql", "mongoose"],
            "redis": ["nosql", "caching"],
            "devops": ["docker", "kubernetes", "jenkins", "ci/cd", "terraform", "ansible"],
            "docker": ["kubernetes", "containerization", "devops"],
            "kubernetes": ["docker", "k8s", "helm", "devops"],
            "ci/cd": ["jenkins", "github actions", "gitlab ci", "circleci", "devops"],
            "cloud": ["aws", "azure", "gcp", "cloud computing"],
            "aws": ["cloud", "ec2", "s3", "lambda", "dynamodb"],
            "azure": ["cloud", "azure devops", "cosmos db"],
            "gcp": ["cloud", "google cloud", "bigquery"],
            "frontend": ["html", "css", "javascript", "react", "angular", "vue", "ui/ux"],
            "backend": ["api", "rest", "graphql", "microservices", "server", "database"],
            "fullstack": ["frontend", "backend", "database", "api"],
            "mobile": ["ios", "android", "react native", "flutter", "swift", "kotlin"],
            "ios": ["swift", "objective-c", "xcode", "mobile"],
            "android": ["kotlin", "java", "android studio", "mobile"],
            "react native": ["react", "mobile", "javascript"],
            "flutter": ["dart", "mobile"],
            "machine learning": ["python", "tensorflow", "pytorch", "scikit-learn", "ai"],
            "data science": ["python", "r", "pandas", "numpy", "statistics", "machine learning"],
            "ai": ["machine learning", "deep learning", "neural networks", "python"],
        }

        # Check for related skills
        for user_skill in user_skills:
            if user_skill in relations:
                for related in relations[user_skill]:
                    if related in required_skills:
                        related_matches.add(f"{user_skill}→{related}")
            
            # Check reverse relations
            for req_skill in required_skills:
                if req_skill in relations and user_skill in relations[req_skill]:
                    related_matches.add(f"{user_skill}←{req_skill}")

        return related_matches

    def _save_matches(self, user_id: int, matched_jobs: List[Dict]):
        try:
            # Clear existing matches for user
            self.db.query(Match).filter(Match.user_id == user_id).delete()
            
            # Save new matches
            for job in matched_jobs:
                match = Match(
                    user_id=user_id,
                    job_id=job["job_id"],
                    score=job["match_score"]
                    # Removed matched_at since it doesn't exist in the model
                )
                self.db.add(match)
            
            self.db.commit()
            logger.info(f"Saved {len(matched_jobs)} matches for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving matches: {str(e)}")
            self.db.rollback()
            raise

    def get_user_matches(self, user_id: int, min_score: float = 0.0) -> List[Dict]:
        """Get saved matches for a user."""
        try:
            matches = (
                self.db.query(Match, Job)
                .join(Job, Match.job_id == Job.id)
                .filter(Match.user_id == user_id)
                .filter(Match.score >= min_score)
                .order_by(Match.score.desc())
                .all()
            )
            
            result = []
            for match, job in matches:
                result.append({
                    "job_id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "remote": job.remote,
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "match_score": match.score,
                    # Removed matched_at since it doesn't exist
                    "url": job.url,
                    "created_at": job.created_at  # Use job's created_at instead
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user matches: {str(e)}")
            return []