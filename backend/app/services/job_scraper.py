# app/services/job_scraper.py
import urllib3
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
from sqlalchemy.orm import Session
# from app.db.models import Job, JobType, ExperienceLevel
from app.db.models import Job, JobTypeEnum as JobType, ExperienceLevel
from app.core.cache import cache_manager

logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class JobScraperService:
    """
    Scrape jobs from multiple free APIs
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Resume-HitHub Job Aggregator)'
        }
    
    def scrape_all_sources(self) -> Dict:
        """
        Scrape jobs from all configured sources
        """
        results = {
            "arbeitnow": 0,  
            "remotive": 0,
            "adzuna": 0,
            "theirstack": 0,
            "errors": []
        }
        
        # 1. Scrape Remotive (no API key needed)
        try:
            arbeitnow_jobs = self.scrape_arbeitnow_jobs()
            results["arbeitnow"] = arbeitnow_jobs
        except Exception as e:
            logger.error(f"Arbeitnow scraping failed: {e}")
            results["errors"].append(f"Arbeitnow: {str(e)}")
        try:
            remotive_jobs = self.scrape_remotive_jobs()
            results["remotive"] = remotive_jobs
        except Exception as e:
            logger.error(f"Remotive scraping failed: {e}")
            results["errors"].append(f"Remotive: {str(e)}")
        
        # 2. Scrape Adzuna (free tier available)
        try:
            adzuna_jobs = self.scrape_adzuna_jobs()
            results["adzuna"] = adzuna_jobs
        except Exception as e:
            logger.error(f"Adzuna scraping failed: {e}")
            results["errors"].append(f"Adzuna: {str(e)}")
        
        # 3. Scrape TheirStack (free API)
        try:
            theirstack_jobs = self.scrape_theirstack_jobs()
            results["theirstack"] = theirstack_jobs
        except Exception as e:
            logger.error(f"TheirStack scraping failed: {e}")
            results["errors"].append(f"TheirStack: {str(e)}")
        
        # Invalidate job match caches after new jobs
        cache_manager.delete_pattern("user:matches:*")
        
        return results
    
    def scrape_remotive_jobs(self, limit: int = 50) -> int:
        """
        Scrape jobs from Remotive.io (completely free, no auth needed)
        """
        url = "http://remotive.io/api/remote-jobs"
        params = {"limit": limit, "category": "software-dev"}
    
        for attempt in range(3):
            try:
                logger.info(f"[Remotive] Fetching jobs (attempt {attempt+1})...")
                response = requests.get(url, headers=self.headers, params=params, timeout=10, verify=False)
                if response.status_code == 526:
                    logger.error("[Remotive] Cloudflare SSL error (526). Skipping Remotive.")
                    return 0
                response.raise_for_status()
            
                jobs = response.json().get("jobs", [])
                added = sum(self._save_remotive_job(job) for job in jobs)
                logger.info(f"[Remotive] ✅ Added {added} jobs.")
                return added
            
            except requests.RequestException as e:
                logger.warning(f"[Remotive] Attempt {attempt+1} failed: {e}")
                logger.error(f"SSL Error with Remotive: {e}")
                logger.info("Remotive API is having SSL issues, skipping...")
                return 0

    
        logger.error("[Remotive] ❌ All attempts failed.")
        return 0
    
    def _save_remotive_job(self, job_data: Dict) -> bool:
        """
        Save a Remotive job to database
        """
        try:
            # Check if job already exists
            external_id = f"remotive_{job_data['id']}"
            existing = self.db.query(Job).filter_by(external_id=external_id).first()
            
            if existing:
                logger.debug(f"Job already exists: {external_id}")
                return False
            
            # Extract and clean data
            title = job_data.get("title", "")
            company = job_data.get("company_name", "Unknown")
            
            # Parse skills from job title and description
            description = job_data.get("description", "")
            required_skills = self._extract_skills_from_text(title + " " + description)
            
            # Parse salary if available
            salary_min, salary_max = self._parse_salary(job_data.get("salary", ""))
            
            # Determine experience level from title
            experience_level = self._determine_experience_level(title)
            
            
            # Create job
            job = Job(
                title=title,
                company=company,
                location=job_data.get("candidate_required_location", "Remote"),
                description=description[:5000],  # Limit description length
                required_skills=", ".join(required_skills),
                url=job_data.get("url", ""),
                remote=True,  # Remotive only has remote jobs
                salary_min=salary_min,
                salary_max=salary_max,
                job_type=JobType.FULL_TIME,
                experience_level=experience_level,
                source="remotive",
                external_id=external_id,
                company_logo_url=job_data.get("company_logo_url", ""),
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            
            self.db.add(job)
            self.db.commit()
            
            logger.info(f"Added job: {title} at {company}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving Remotive job: {e}")
            self.db.rollback()
            return False
        
    def scrape_arbeitnow_jobs(self, limit: int = 50) -> int:

        url = "https://www.arbeitnow.com/api/job-board-api"
        
        try:
            logger.info("Fetching jobs from Arbeitnow...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get("data", [])[:limit]
            
            added_count = 0
            for job_data in jobs:
                if self._save_arbeitnow_job(job_data):
                    added_count += 1
            
            logger.info(f"Added {added_count} jobs from Arbeitnow")
            return added_count
            
        except Exception as e:
            logger.error(f"Error scraping Arbeitnow: {e}")
            return 0

    def _save_arbeitnow_job(self, job_data: Dict) -> bool:
        """Save Arbeitnow job"""
        try:
            external_id = f"arbeitnow_{job_data.get('slug', 'unknown')}"
            existing = self.db.query(Job).filter_by(external_id=external_id).first()
            
            if existing:
                return False
            
            # Extract skills from tags
            tags = job_data.get('tags', [])
            
            job = Job(
                title=job_data.get('title', ''),
                company=job_data.get('company_name', 'Unknown'),
                location=job_data.get('location', 'Remote'),
                description=job_data.get('description', '')[:5000],
                required_skills=', '.join(tags),
                url=job_data.get('url', ''),
                remote=job_data.get('remote', False),
                source="arbeitnow",
                external_id=external_id,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            
            self.db.add(job)
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving Arbeitnow job: {e}")
            self.db.rollback()
            return False
    
    def scrape_adzuna_jobs(self, limit: int = 50) -> int:
        """
        Scrape jobs from Adzuna (requires free API key)
        Get your free key at: https://developer.adzuna.com/
        """
        # You need to sign up for free API keys
        APP_ID = "your_adzuna_app_id"  # Replace with your ID
        APP_KEY = "your_adzuna_app_key"  # Replace with your key
        
        if APP_ID == "your_adzuna_app_id":
            logger.warning("Adzuna API keys not configured. Skipping...")
            return 0
        
        url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "results_per_page": limit,
            "what": "software developer",  # Search term
            "content-type": "application/json"
        }
        
        try:
            logger.info("Fetching jobs from Adzuna...")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            jobs = data.get("results", [])
            
            added_count = 0
            for job_data in jobs:
                if self._save_adzuna_job(job_data):
                    added_count += 1
            
            logger.info(f"Added {added_count} jobs from Adzuna")
            return added_count
            
        except Exception as e:
            logger.error(f"Error scraping Adzuna: {e}")
            return 0
    
    def _save_adzuna_job(self, job_data: Dict) -> bool:
        """Save an Adzuna job to database"""
        try:
            external_id = f"adzuna_{job_data['id']}"
            existing = self.db.query(Job).filter_by(external_id=external_id).first()
            
            if existing:
                return False
            
            title = job_data.get("title", "")
            company = job_data.get("company", {}).get("display_name", "Unknown")
            description = job_data.get("description", "")
            
            # Extract skills
            required_skills = self._extract_skills_from_text(title + " " + description)
            
            # Parse salary
            salary_min = job_data.get("salary_min", 0)
            salary_max = job_data.get("salary_max", 0)
            
            job = Job(
                title=title,
                company=company,
                location=job_data.get("location", {}).get("display_name", "Unknown"),
                description=description[:5000],
                required_skills=", ".join(required_skills),
                url=job_data.get("redirect_url", ""),
                remote="remote" in title.lower() or "remote" in description.lower(),
                salary_min=salary_min,
                salary_max=salary_max,
                job_type=JobType.FULL_TIME if "full time" in description.lower() else JobType.CONTRACT,
                source="adzuna",
                external_id=external_id,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            
            self.db.add(job)
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving Adzuna job: {e}")
            self.db.rollback()
            return False
    
    def scrape_theirstack_jobs(self, limit: int = 30) -> int:
        """
        Scrape jobs from TheirStack (free, no auth)
        """
        url = "https://api.theirstack.com/v1/jobs"
        
        try:
            logger.info("Fetching jobs from TheirStack...")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            jobs = response.json()[:limit]
            
            added_count = 0
            for job_data in jobs:
                if self._save_theirstack_job(job_data):
                    added_count += 1
                    time.sleep(0.5)  # Be respectful with rate limiting
            
            logger.info(f"Added {added_count} jobs from TheirStack")
            return added_count
            
        except Exception as e:
            logger.error(f"Error scraping TheirStack: {e}")
            return 0
    
    def _save_theirstack_job(self, job_data: Dict) -> bool:
        """Save a TheirStack job"""
        try:
            external_id = f"theirstack_{job_data.get('id', 'unknown')}"
            existing = self.db.query(Job).filter_by(external_id=external_id).first()
            
            if existing:
                return False
            
            title = job_data.get("title", "")
            company = job_data.get("company", "Unknown")
            
            # Extract skills from tags
            tags = job_data.get("tags", [])
            required_skills = [tag for tag in tags if tag.lower() in self._get_known_skills()]
            
            job = Job(
                title=title,
                company=company,
                location=job_data.get("location", "Unknown"),
                description=job_data.get("description", "")[:5000],
                required_skills=", ".join(required_skills),
                url=job_data.get("url", ""),
                remote=job_data.get("remote", False),
                source="theirstack",
                external_id=external_id,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            
            self.db.add(job)
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving TheirStack job: {e}")
            self.db.rollback()
            return False
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extract technical skills from job text
        """
        text_lower = text.lower()
        found_skills = []
        
        # Common technical skills to look for
        skill_keywords = [
            # Languages
            'python', 'javascript', 'java', 'c++', 'c#', 'ruby', 'go', 'rust', 'php', 'swift',
            'typescript', 'kotlin', 'scala', 'r', 'matlab', 'perl',
            
            # Frontend
            'react', 'angular', 'vue', 'svelte', 'html', 'css', 'sass', 'jquery',
            'webpack', 'babel', 'next.js', 'nuxt.js', 'gatsby',
            
            # Backend
            'node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'rails',
            '.net', 'laravel', 'symfony',
            
            # Databases
            'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
            'cassandra', 'dynamodb', 'oracle', 'sqlite',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform',
            'ansible', 'gitlab', 'circleci', 'travis ci',
            
            # Other
            'git', 'linux', 'rest api', 'graphql', 'microservices', 'ci/cd',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch'
        ]
        
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill)
        
        return list(set(found_skills))[:10]  # Return max 10 skills
    
    def _parse_salary(self, salary_str: str) -> tuple[Optional[int], Optional[int]]:
        """
        Parse salary string to min/max values
        """
        if not salary_str:
            return None, None
        
        import re
        
        # Look for numbers in the string
        numbers = re.findall(r'\$?(\d{1,3}(?:,\d{3})*(?:k)?)', salary_str)
        
        if not numbers:
            return None, None
        
        # Convert to integers
        salaries = []
        for num in numbers:
            num = num.replace(',', '').replace('$', '')
            if 'k' in num.lower():
                salaries.append(int(float(num.replace('k', '')) * 1000))
            else:
                value = int(num)
                # Assume numbers less than 1000 are in thousands
                if value < 1000:
                    value *= 1000
                salaries.append(value)
        
        if len(salaries) >= 2:
            return min(salaries), max(salaries)
        elif len(salaries) == 1:
            return salaries[0], salaries[0]
        
        return None, None
    
    def _determine_experience_level(self, title: str) -> ExperienceLevel:
        """
        Determine experience level from job title
        """
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['senior', 'sr.', 'lead', 'principal']):
            return ExperienceLevel.SENIOR
        elif any(word in title_lower for word in ['junior', 'jr.', 'entry']):
            return ExperienceLevel.JUNIOR
        elif any(word in title_lower for word in ['mid-level', 'mid level']):
            return ExperienceLevel.MID
        else:
            return ExperienceLevel.MID  # Default
    
    def _get_known_skills(self) -> set:
        """Get list of known skills for matching"""
        return {
            'python', 'javascript', 'java', 'react', 'angular', 'vue',
            'django', 'flask', 'node.js', 'express', 'sql', 'mongodb',
            'aws', 'docker', 'kubernetes', 'git', 'api', 'rest'
        }