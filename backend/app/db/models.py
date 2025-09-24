from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, DateTime, Boolean, JSON, func
from enum import Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from sqlalchemy import Enum as SqlEnum, Column, Integer, String

Base = declarative_base()

class JobTypeEnum(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    INTERNSHIP = "internship"
    CONTRACT = "contract"

class ExperienceLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    github_username = Column(String, unique=True, nullable=True)
    resume_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    skills = relationship("Skill", back_populates="user")
    matches = relationship("Match", back_populates="user")
    tasks = relationship("TaskStatus", back_populates="user")
    profile = relationship("Profile", back_populates="user", uselist=False)

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="skills")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    required_skills = Column(Text, nullable=True)
    remote = Column(Boolean, default=False)  # Add this
    salary_min = Column(Integer, nullable=True)  # Add this
    salary_max = Column(Integer, nullable=True)  # Add this
    external_id = Column(String, unique=True, index=True)   
    source = Column(String, nullable=True)                  
    company_logo_url = Column(String, nullable=True)       
    expires_at = Column(DateTime, nullable=True)
    job_type = Column(SqlEnum(JobTypeEnum), nullable=False)
    experience_level = Column(SqlEnum(ExperienceLevel), nullable=True)
    url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    matches = relationship("Match", back_populates="job")
    


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    score = Column(Float, nullable=False)

    user = relationship("User", back_populates="matches")
    job = relationship("Job", back_populates="matches")

class SkillMaster(Base):
    __tablename__ = "skills_master"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String, nullable=True)  
    source = Column(String, default="manual")  
    is_verified = Column(Boolean, default=False)  

class TaskStatus(Base):
    """Track background task status"""
    __tablename__ = "task_status"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)  # Celery task ID
    user_id = Column(Integer, ForeignKey("users.id"))
    task_type = Column(String)  # resume_processing, github_analysis, etc.
    status = Column(String, default="pending")  # pending, processing, completed, failed
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="tasks")

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    full_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    location = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    
    linkedin_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    github_username = Column(String(100), nullable=True)
    
    resume_path = Column(String(500), nullable=True)
    resume_uploaded_at = Column(DateTime(timezone=True), nullable=True)
    
    skills = Column(Text, nullable=True)  
    
    is_complete = Column(Boolean, default=False)
    completion_percentage = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="profile")
    
    def calculate_completion(self):
        """Calculate profile completion percentage"""
        fields = [
            self.full_name,
            self.phone,
            self.location,
            self.title,
            self.bio,
            self.linkedin_url,
            self.resume_path,
            self.skills
        ]
        filled = sum(1 for field in fields if field)
        return int((filled / len(fields)) * 100)
