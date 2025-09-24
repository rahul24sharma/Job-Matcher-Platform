import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.db.models import SkillMaster

load_dotenv()
logger = logging.getLogger(__name__)


class GitHubAnalyzer:
    def __init__(self, db: Session):
        self.db = db
        self.base_url = "https://api.github.com"

        # Auth / headers
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

        # Fast, resilient HTTP session
        self.session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

        # Load canonical skills once
        self._load_skills()

    # ------------------------
    # Public API
    # ------------------------
    def analyze_profile(self, username: str) -> Dict:
        """Analyze a GitHub profile and extract skills."""
        try:
            user_info = self._get_user_info(username)
            if not user_info:
                raise ValueError(f"GitHub user {username} not found")

            repos = self._get_repositories(username)
            languages = self._analyze_languages(repos)
            repo_skills = self._extract_skills_from_repos(repos, username)
            top_repos = self._get_top_repositories(repos)
            activity_score = self._calculate_activity_score(repos, user_info)

            # Combine skills (languages + repo-derived)
            all_skills = set(languages.keys()) | set(repo_skills)

            # Map to known skills in DB (case-insensitive)
            matched_skills: List[str] = []
            for s in all_skills:
                key = s.lower()
                if key in self.known_skills:
                    matched_skills.append(self.known_skills[key])

            result = {
                "username": username,
                "profile": {
                    "name": user_info.get("name") or username,
                    "bio": user_info.get("bio") or "",
                    "company": user_info.get("company") or "",
                    "location": user_info.get("location") or "",
                    "public_repos": user_info.get("public_repos", 0),
                    "followers": user_info.get("followers", 0),
                    "following": user_info.get("following", 0),
                    "created_at": user_info.get("created_at", ""),
                    "avatar_url": user_info.get("avatar_url", ""),
                },
                "languages": languages,  # {lang: count_of_repos_using_it}
                "skills": sorted(list(set(matched_skills))),
                "top_repositories": top_repos[:10],  # simplified payload
                "activity_score": activity_score,
                "total_stars": sum(r.get("stargazers_count", 0) for r in repos),
                "total_forks": sum(r.get("forks_count", 0) for r in repos),
            }
            return result

        except Exception as e:
            logger.error(f"Error analyzing GitHub profile {username}: {str(e)}")
            raise

    # ------------------------
    # Internals
    # ------------------------
    def _load_skills(self):
        """Load skills from SkillMaster as canonical set."""
        skills = self.db.query(SkillMaster.name).all()
        # map lower -> canonical
        self.known_skills = {row[0].strip().lower(): row[0].strip() for row in skills if row and row[0]}
        logger.info(f"Loaded {len(self.known_skills)} skills for matching")

    def _get(self, url: str, **kwargs):
        return self.session.get(url, headers=self.headers, timeout=10, **kwargs)

    def _get_user_info(self, username: str) -> Optional[Dict]:
        r = self._get(f"{self.base_url}/users/{username}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def _get_repositories(self, username: str) -> List[Dict]:
        """Fetch repositories quickly: skip forks, limit pages."""
        repos: List[Dict] = []
        page = 1
        while True:
            r = self._get(
                f"{self.base_url}/users/{username}/repos",
                params={"page": page, "per_page": 100, "sort": "updated"},
            )
            r.raise_for_status()
            data = r.json()
            if not data:
                break

            # Skip forks to reduce noise and calls
            data = [d for d in data if not d.get("fork")]
            repos.extend(data)

            # Hard limits to keep analysis snappy
            if page >= 2 or len(repos) >= 200:
                break
            page += 1

        return repos

    def _analyze_languages(self, repos: List[Dict]) -> Dict[str, int]:
        """Count how many repos use each primary language."""
        stats: Dict[str, int] = {}
        for repo in repos:
            lang = repo.get("language")
            if lang:
                stats[lang] = stats.get(lang, 0) + 1
        # Sort by usage desc
        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

    def _extract_skills_from_repos(self, repos: List[Dict], username: str) -> Set[str]:
        """Find skills from repo name/description/topics (no heavy file calls)."""
        skills: Set[str] = set()
        patterns = {
            "react": r"\breact\b",
            "angular": r"\bangular\b",
            "vue": r"\bvue\b",
            "fastapi": r"\bfastapi\b",
            "flask": r"\bflask\b",
            "django": r"\bdjango\b",
            "express": r"\bexpress\b",
            "spring": r"\bspring\b",
            "docker": r"\bdocker\b",
            "kubernetes": r"\bkubernetes\b|k8s",
            "graphql": r"\bgraphql\b",
            "mongodb": r"\bmongodb\b|mongo",
            "postgresql": r"\bpostgresql\b|\bpostgres\b",
            "redis": r"\bredis\b",
            "ci/cd": r"ci\/cd|continuous integration",
            "microservices": r"\bmicroservices?\b",
            "aws": r"\baws\b|amazon web services",
            "machine learning": r"machine[\s-]?learning|ml",
        }

        # Limit scanned repos to keep performance predictable
        for repo in repos[:100]:
            name = (repo.get("name") or "").lower()
            desc = (repo.get("description") or "").lower()
            topics = [t.lower() for t in (repo.get("topics") or [])]
            combined = f"{name} {desc} {' '.join(topics)}"

            for label, pat in patterns.items():
                if re.search(pat, combined):
                    skills.add(label)

            for t in topics:
                if len(t) > 2:
                    skills.add(t)

        # Heavy file checks disabled to save time
        # for repo in repos[:3]:
        #     skills.update(self._check_repo_files(username, repo["name"]))

        return skills

    def _get_top_repositories(self, repos: List[Dict]) -> List[Dict]:
        """Score and select top repos (lightweight)."""
        scored = []
        for repo in repos:
            score = 0
            score += repo.get("stargazers_count", 0) * 2
            score += repo.get("forks_count", 0) * 3

            if repo.get("updated_at"):
                updated = datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00"))
                days = (datetime.now(updated.tzinfo) - updated).days
                if days < 30:
                    score += 20
                elif days < 90:
                    score += 10

            if repo.get("description"):
                score += 5
            if not repo.get("fork"):
                score += 10

            scored.append((score, repo))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = []
        for _, r in scored[:10]:
            top.append({
                "name": r["name"],
                "description": r.get("description", ""),
                "language": r.get("language", "Unknown"),
                "stargazers_count": r.get("stargazers_count", 0),
                "forks_count": r.get("forks_count", 0),
                "html_url": r["html_url"],
                "updated_at": r.get("updated_at", ""),
            })
        return top

    def _calculate_activity_score(self, repos: List[Dict], user_info: Dict) -> float:
        """0-100 score from repos, stars, forks, recency, age & followers."""
        score = 0.0

        repo_count = len([r for r in repos if not r.get("fork")])
        score += min(repo_count * 2, 20)

        total_stars = sum(r.get("stargazers_count", 0) for r in repos)
        score += min(total_stars / 10, 20)

        total_forks = sum(r.get("forks_count", 0) for r in repos)
        score += min(total_forks / 5, 20)

        recent = 0
        for r in repos:
            if r.get("updated_at"):
                updated = datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00"))
                if (datetime.now(updated.tzinfo) - updated).days < 90:
                    recent += 1
        score += min(recent * 2, 20)

        if user_info.get("created_at"):
            created = datetime.fromisoformat(user_info["created_at"].replace("Z", "+00:00"))
            days = (datetime.now(created.tzinfo) - created).days
            if days > 365:
                score += 10

        followers = user_info.get("followers", 0)
        score += min(followers / 10, 10)

        return min(score, 100)
