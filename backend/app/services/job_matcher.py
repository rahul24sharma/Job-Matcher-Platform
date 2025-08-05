from typing import List, Dict, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import or_
import re
from datetime import datetime
import logging

from app.db.models import User, Skill, Job, Match
from app.db.models import SkillMaster

logger = logging.getLogger(__name__)

class JobMatcher:
    def __init__(self, db: Session):
        self.db = db
        
    def match_jobs_for_user(self, user_id: int) -> List[Dict]:
        """
        Main method to match jobs for a user based on their skills
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            return []
        
        # Get user's skills (both resume and GitHub)
        user_skills = self._get_user_skills(user_id)
        if not user_skills:
            logger.info(f"User {user_id} has no skills")
            return []
        
        # Get all active jobs
        jobs = self.db.query(Job).all()
        if not jobs:
            logger.info("No jobs in database")
            return []
        
        matched_jobs = []
        for job in jobs:
            match_score, match_reasons = self._calculate_match_score(
                user_skills, 
                job,
                user
            )
            
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
        
        # Sort by match score (highest first)
        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Save top matches to database
        self._save_matches(user_id, matched_jobs[:50])  # Save top 50
        
        return matched_jobs
    
    def _get_user_skills(self, user_id: int) -> Set[str]:
        """Get all skills for a user (resume + GitHub)"""
        skills = self.db.query(Skill).filter(Skill.user_id == user_id).all()
        
        user_skills = set()
        for skill in skills:
            # Remove 'github_' prefix if present
            skill_name = skill.name.replace('github_', '') if skill.name.startswith('github_') else skill.name
            user_skills.add(skill_name.lower())
        
        logger.info(f"User {user_id} has {len(user_skills)} unique skills")
        return user_skills
    
    def _calculate_match_score(self, user_skills: Set[str], job: Job, user: User) -> Tuple[float, List[str]]:
        """
        Calculate match score between user skills and job requirements
        Returns: (score 0-100, list of reasons)
        """
        score = 0.0
        reasons = []
        
        # Parse job required skills
        job_skills = set()
        if job.required_skills:
            # Split by common delimiters
            skills_list = re.split(r'[,;|]+', job.required_skills)
            job_skills = {skill.strip().lower() for skill in skills_list if skill.strip()}
        
        if not job_skills:
            return 0.0, ["No skills specified for this job"]
        
        # 1. Skill Matching (70% weight)
        matched_skills = user_skills.intersection(job_skills)
        skill_match_ratio = len(matched_skills) / len(job_skills) if job_skills else 0
        skill_score = skill_match_ratio * 70
        score += skill_score
        
        if matched_skills:
            skills_list = sorted(list(matched_skills))[:5]  # Show top 5
            reasons.append(f"Matching skills: {', '.join(skills_list)}")
        
        # 2. Related Skills Matching (10% weight)
        related_matches = self._find_related_skills(user_skills, job_skills - matched_skills)
        if related_matches:
            score += len(related_matches) * 2  # 2 points per related skill, max 10
            reasons.append(f"Related skills: {', '.join(list(related_matches)[:3])}")
        
        # 3. Location Matching (10% weight)
        if user.github_username:  # Use GitHub location if available
            # For now, simple check - you can enhance this
            if job.location and "Boston" in job.location:
                score += 10
                reasons.append("Location match (Boston)")
        
        # 4. Experience Level Matching (10% weight)
        # Infer from job title
        job_title_lower = job.title.lower()
        
        # Simple heuristic based on number of skills
        user_skill_count = len(user_skills)
        
        if "senior" in job_title_lower or "lead" in job_title_lower:
            if user_skill_count >= 15:
                score += 10
                reasons.append("Experience level match (Senior)")
        elif "junior" in job_title_lower or "entry" in job_title_lower:
            if user_skill_count <= 10:
                score += 10
                reasons.append("Experience level match (Junior)")
        else:  # Mid-level
            if 8 <= user_skill_count <= 20:
                score += 10
                reasons.append("Experience level match")
        
        # 5. Bonus for high skill coverage
        if skill_match_ratio >= 0.8:
            score += 5
            reasons.append("Excellent skill match (80%+)")
        elif skill_match_ratio >= 0.6:
            score += 3
            reasons.append("Strong skill match (60%+)")
        
        # Ensure score doesn't exceed 100
        score = min(score, 100.0)
        
        # Round to 2 decimal places
        score = round(score, 2)
        
        return score, reasons
    
    def _find_related_skills(self, user_skills: Set[str], required_skills: Set[str]) -> Set[str]:
        """Find related skills that might qualify the user"""
        related_matches = set()
        
        # Define skill relationships
        skill_relations = {
            # Languages
            'python': ['django', 'flask', 'fastapi', 'pandas', 'numpy'],
            'javascript': ['react', 'angular', 'vue', 'node.js', 'express', 'typescript'],
            'java': ['spring', 'spring boot', 'hibernate'],
            
            # Databases
            'sql': ['postgresql', 'mysql', 'sqlite'],
            'nosql': ['mongodb', 'redis', 'cassandra'],
            
            # DevOps
            'devops': ['docker', 'kubernetes', 'jenkins', 'ci/cd'],
            'cloud': ['aws', 'azure', 'gcp'],
            
            # General
            'frontend': ['html', 'css', 'javascript', 'react', 'angular', 'vue'],
            'backend': ['api', 'rest', 'graphql', 'microservices'],
            'fullstack': ['frontend', 'backend', 'database'],
        }
        
        # Check both directions
        for user_skill in user_skills:
            # Check if user skill is related to required skills
            if user_skill in skill_relations:
                for related in skill_relations[user_skill]:
                    if related in required_skills:
                        related_matches.add(f"{user_skill}→{related}")
            
            # Check if required skills are related to user skills
            for req_skill in required_skills:
                if req_skill in skill_relations and user_skill in skill_relations[req_skill]:
                    related_matches.add(f"{user_skill}→{req_skill}")
        
        return related_matches
    
    def _save_matches(self, user_id: int, matched_jobs: List[Dict]):
        """Save job matches to database"""
        try:
            # Delete existing matches for user
            self.db.query(Match).filter(Match.user_id == user_id).delete()
            
            # Add new matches
            for job_data in matched_jobs:
                match = Match(
                    user_id=user_id,
                    job_id=job_data['job_id'],
                    score=job_data['match_score']
                )
                self.db.add(match)
            
            self.db.commit()
            logger.info(f"Saved {len(matched_jobs)} matches for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error saving matches: {str(e)}")
            self.db.rollback()
    
    def get_match_statistics(self, user_id: int) -> Dict:
        """Get statistics about user's job matches"""
        matches = self.db.query(Match).filter(Match.user_id == user_id).all()
        
        if not matches:
            return {
                "total_matches": 0,
                "average_score": 0,
                "top_match_score": 0,
                "match_distribution": {}
            }
        
        scores = [match.score for match in matches]
        
        # Calculate distribution
        distribution = {
            "excellent": len([s for s in scores if s >= 80]),
            "strong": len([s for s in scores if 60 <= s < 80]),
            "good": len([s for s in scores if 40 <= s < 60]),
            "fair": len([s for s in scores if 20 <= s < 40]),
            "low": len([s for s in scores if s < 20])
        }
        
        return {
            "total_matches": len(matches),
            "average_score": round(sum(scores) / len(scores), 2),
            "top_match_score": round(max(scores), 2),
            "match_distribution": distribution
        }
    
    def get_top_matches(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get top job matches for a user"""
        matches = self.db.query(Match, Job).join(
            Job, Match.job_id == Job.id
        ).filter(
            Match.user_id == user_id
        ).order_by(
            Match.score.desc()
        ).limit(limit).all()
        
        results = []
        for match, job in matches:
            results.append({
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "match_score": match.score,
                "salary_range": f"${job.salary_min:,} - ${job.salary_max:,}" if job.salary_min else "Not specified",
                "remote": job.remote,
                "url": job.url
            })
        
        return results