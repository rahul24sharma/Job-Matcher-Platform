import re
from typing import Dict, List

class ResumeParser:
    def parse_resume(self, file_content: bytes, filename: str) -> Dict:
        """
        Parse resume and extract skills
        (This is a simplified version - you can enhance with libraries like pdfplumber, python-docx, etc.)
        """
        # Convert bytes to text (simple approach)
        try:
            text = file_content.decode('utf-8', errors='ignore')
        except:
            text = str(file_content)
        
        # Extract skills (simple keyword matching - enhance this!)
        skills = self._extract_skills(text)
        
        return {
            "text": text,
            "skills": skills,
            "filename": filename
        }
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        # Common programming skills (expand this list)
        skill_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'django', 'flask', 'fastapi', 'spring', 'node.js', 'express',
            'sql', 'postgresql', 'mysql', 'mongodb', 'redis',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp',
            'git', 'ci/cd', 'jenkins', 'github actions',
            'machine learning', 'data science', 'tensorflow', 'pytorch',
            'html', 'css', 'sass', 'tailwind',
            'rest api', 'graphql', 'microservices',
            'agile', 'scrum', 'jira'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill)
        
        return list(set(found_skills))  