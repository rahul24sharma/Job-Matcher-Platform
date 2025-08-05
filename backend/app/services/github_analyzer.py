import requests
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import re
import os
from dotenv import load_dotenv

from app.db.models import SkillMaster, User, Skill
load_dotenv()

logger = logging.getLogger(__name__)

class GitHubAnalyzer:
    def __init__(self, db: Session):
        self.db = db
        self.base_url = "https://api.github.com"
        
        # Get token from environment variable
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        
        # Load skills from database for matching
        self._load_skills()
    
    def _load_skills(self):
        """Load all skills from database for matching"""
        skills = self.db.query(SkillMaster.name).all()
        self.known_skills = {skill[0].lower(): skill[0] for skill in skills}
        logger.info(f"Loaded {len(self.known_skills)} skills for matching")
    
    def analyze_profile(self, username: str) -> Dict:
        """
        Analyze a GitHub profile and extract skills
        """
        try:
            # Get user info
            user_info = self._get_user_info(username)
            if not user_info:
                raise ValueError(f"GitHub user {username} not found")
            
            # Get repositories
            repos = self._get_repositories(username)
            
            # Analyze data
            languages = self._analyze_languages(repos)
            repo_skills = self._extract_skills_from_repos(repos, username)
            top_repos = self._get_top_repositories(repos)
            activity_score = self._calculate_activity_score(repos, user_info)
            
            # Combine all skills found
            all_skills = set()
            all_skills.update(languages.keys())  # Add languages as skills
            all_skills.update(repo_skills)
            
            # Match against known skills in database
            matched_skills = []
            for skill in all_skills:
                skill_lower = skill.lower()
                if skill_lower in self.known_skills:
                    matched_skills.append(self.known_skills[skill_lower])
            
            return {
                "username": username,
                "profile": {
                    "name": user_info.get("name", username),
                    "bio": user_info.get("bio", ""),
                    "company": user_info.get("company", ""),
                    "location": user_info.get("location", ""),
                    "public_repos": user_info.get("public_repos", 0),
                    "followers": user_info.get("followers", 0),
                    "following": user_info.get("following", 0),
                    "created_at": user_info.get("created_at", "")
                },
                "languages": languages,
                "skills": sorted(list(set(matched_skills))),
                "top_repositories": top_repos[:10],
                "activity_score": activity_score,
                "total_stars": sum(repo.get("stargazers_count", 0) for repo in repos),
                "total_forks": sum(repo.get("forks_count", 0) for repo in repos)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing GitHub profile {username}: {str(e)}")
            raise
    
    def _get_user_info(self, username: str) -> Optional[Dict]:
        """Get basic user information"""
        try:
            response = requests.get(
                f"{self.base_url}/users/{username}",
                headers=self.headers
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching user info: {str(e)}")
            return None
    
    def _get_repositories(self, username: str) -> List[Dict]:
        """Get all user repositories"""
        repos = []
        page = 1
        
        while True:
            try:
                response = requests.get(
                    f"{self.base_url}/users/{username}/repos",
                    headers=self.headers,
                    params={
                        "page": page,
                        "per_page": 100,
                        "sort": "updated"
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                if not data:
                    break
                
                repos.extend(data)
                
                # Limit to prevent too many API calls
                if page >= 3 or len(repos) >= 300:
                    break
                
                page += 1
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching repositories: {str(e)}")
                break
        
        return repos
    
    def _analyze_languages(self, repos: List[Dict]) -> Dict[str, int]:
        """Analyze programming languages used"""
        language_stats = {}
        
        for repo in repos:
            if repo.get("language"):
                lang = repo["language"]
                language_stats[lang] = language_stats.get(lang, 0) + 1
        
        # Sort by usage
        return dict(sorted(language_stats.items(), key=lambda x: x[1], reverse=True))
    
    def _extract_skills_from_repos(self, repos: List[Dict], username: str) -> Set[str]:

        """Extract skills from repository names, descriptions, and topics"""
        skills = set()
        
        # Common framework/tool patterns
        patterns = {
            'react': r'\breact\b',
            'angular': r'\bangular\b',
            'vue': r'\bvue\b',
            'django': r'\bdjango\b',
            'flask': r'\bflask\b',
            'fastapi': r'\bfastapi\b',
            'express': r'\bexpress\b',
            'spring': r'\bspring\b',
            'docker': r'\bdocker\b',
            'kubernetes': r'\bkubernetes\b|k8s',
            'tensorflow': r'\btensorflow\b|tf',
            'pytorch': r'\bpytorch\b|torch',
            'aws': r'\baws\b|amazon web services',
            'machine learning': r'machine[\s-]?learning|ml',
            'data science': r'data[\s-]?science',
            'api': r'\bapi\b|rest[\s-]?api',
            'graphql': r'\bgraphql\b',
            'mongodb': r'\bmongodb\b|mongo',
            'postgresql': r'\bpostgresql\b|postgres',
            'redis': r'\bredis\b',
            'elasticsearch': r'\belasticsearch\b',
            'jenkins': r'\bjenkins\b',
            'ci/cd': r'ci\/cd|continuous integration',
            'microservices': r'\bmicroservices?\b',
            'blockchain': r'\bblockchain\b',
            'android': r'\bandroid\b',
            'ios': r'\bios\b|iphone|ipad',
            'flutter': r'\bflutter\b',
            'react native': r'react[\s-]?native'
        }
        
        for repo in repos:
            # Check repository name
            repo_name = repo.get("name", "").lower()
            
            # Check description
            description = repo.get("description", "").lower() if repo.get("description") else ""
            
            # Check topics
            topics = repo.get("topics", [])
            
            # Combine all text
            combined_text = f"{repo_name} {description} {' '.join(topics)}".lower()
            
            # Look for patterns
            for skill, pattern in patterns.items():
                if re.search(pattern, combined_text):
                    skills.add(skill)
            
            # Add topics as potential skills
            for topic in topics:
                if len(topic) > 2:  # Skip very short topics
                    skills.add(topic)
            
            # Check for specific files (if we want to make additional API calls)
            # This is optional and uses more API quota
            if repo.get("name") and not repo.get("fork"):
                # Check for common config files
                file_skills = self._check_repo_files(username, repo["name"])
                skills.update(file_skills)
        
        return skills
    
    def _check_repo_files(self, username: str, repo_name: str) -> Set[str]:
        """Check repository files for additional skills (optional, uses more API calls)"""
        skills = set()
        
        # Files that indicate certain technologies
        file_checks = {
            'package.json': ['node.js', 'npm'],
            'requirements.txt': ['python'],
            'Gemfile': ['ruby', 'rails'],
            'pom.xml': ['java', 'maven'],
            'build.gradle': ['gradle'],
            'Dockerfile': ['docker'],
            'docker-compose.yml': ['docker', 'docker-compose'],
            '.github/workflows': ['github actions'],
            'Jenkinsfile': ['jenkins'],
            'serverless.yml': ['serverless'],
            'terraform': ['terraform'],
            'kubernetes': ['kubernetes'],
            'Cargo.toml': ['rust'],
            'go.mod': ['go']
        }
        
        # Only check a few files to save API calls
        for file_path, file_skills in list(file_checks.items())[:5]:
            try:
                response = requests.get(
                    f"{self.base_url}/repos/{username}/{repo_name}/contents/{file_path}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    skills.update(file_skills)
                    
                    # Parse package.json for more skills
                    if file_path == 'package.json':
                        content = response.json()
                        if content.get('content'):
                            # Decode base64 content
                            import base64
                            import json
                            decoded = base64.b64decode(content['content']).decode('utf-8')
                            package_data = json.loads(decoded)
                            
                            # Check dependencies
                            deps = list(package_data.get('dependencies', {}).keys())
                            deps.extend(list(package_data.get('devDependencies', {}).keys()))
                            
                            # Common package to skill mapping
                            package_skills = {
                                'react': 'react',
                                'vue': 'vue',
                                'angular': 'angular',
                                'express': 'express',
                                'next': 'next.js',
                                'typescript': 'typescript',
                                'jest': 'jest',
                                'webpack': 'webpack'
                            }
                            
                            for dep in deps:
                                for package, skill in package_skills.items():
                                    if package in dep.lower():
                                        skills.add(skill)
                                        
            except:
                # Ignore errors for individual file checks
                pass
        
        return skills
    
    def _get_top_repositories(self, repos: List[Dict]) -> List[Dict]:
        """Get top repositories by quality score"""
        # Calculate quality score for each repo
        for repo in repos:
            score = 0
            score += repo.get("stargazers_count", 0) * 2
            score += repo.get("forks_count", 0) * 3
            
            # Recent activity bonus
            if repo.get("updated_at"):
                updated = datetime.fromisoformat(repo["updated_at"].replace('Z', '+00:00'))
                days_ago = (datetime.now(updated.tzinfo) - updated).days
                if days_ago < 30:
                    score += 20
                elif days_ago < 90:
                    score += 10
            
            # Has description
            if repo.get("description"):
                score += 5
            
            # Not a fork
            if not repo.get("fork"):
                score += 10
            
            repo["quality_score"] = score
        
        # Sort by quality score
        sorted_repos = sorted(repos, key=lambda x: x.get("quality_score", 0), reverse=True)
        
        # Return simplified repo data
        top_repos = []
        for repo in sorted_repos[:10]:
            top_repos.append({
                "name": repo["name"],
                "description": repo.get("description", ""),
                "language": repo.get("language", "Unknown"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "url": repo["html_url"],
                "updated_at": repo.get("updated_at", "")
            })
        
        return top_repos
    
    def _calculate_activity_score(self, repos: List[Dict], user_info: Dict) -> float:
        """Calculate activity score (0-100)"""
        score = 0.0
        
        # Repository count (max 20 points)
        repo_count = len([r for r in repos if not r.get("fork")])
        score += min(repo_count * 2, 20)
        
        # Total stars (max 20 points)
        total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
        score += min(total_stars / 10, 20)
        
        # Total forks (max 20 points)
        total_forks = sum(repo.get("forks_count", 0) for repo in repos)
        score += min(total_forks / 5, 20)
        
        # Recent activity (max 20 points)
        recent_repos = 0
        for repo in repos:
            if repo.get("updated_at"):
                updated = datetime.fromisoformat(repo["updated_at"].replace('Z', '+00:00'))
                if (datetime.now(updated.tzinfo) - updated).days < 90:
                    recent_repos += 1
        score += min(recent_repos * 2, 20)
        
        # Account age and followers (max 20 points)
        if user_info.get("created_at"):
            created = datetime.fromisoformat(user_info["created_at"].replace('Z', '+00:00'))
            account_days = (datetime.now(created.tzinfo) - created).days
            if account_days > 365:
                score += 10
        
        followers = user_info.get("followers", 0)
        score += min(followers / 10, 10)
        
        return min(score, 100)