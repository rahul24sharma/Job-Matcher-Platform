# backend/tests/conftest.py

import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.models import Base
from app.db.session import get_db
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = "postgresql://testuser:testpass@localhost:5432/test_resume_hithub"

# Create test engine
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db() -> Generator:
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    
    db = TestingSessionLocal(bind=connection)
    
    yield db
    
    db.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db) -> Generator:
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    """Create a test user."""
    from app.db.models import User
    from app.core.security import get_password_hash
    
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_job(db):
    """Create a sample job for testing."""
    from app.db.models import Job
    
    job = Job(
        title="Python Developer",
        company="Test Company",
        location="Remote",
        description="We are looking for a Python developer",
        required_skills="Python, Django, PostgreSQL",
        remote=True,
        salary_min=80000,
        salary_max=120000,
        source="test"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return job

@pytest.fixture
def user_with_skills(db, test_user):
    """Create a user with skills."""
    from app.db.models import Skill
    
    skills = [
        Skill(user_id=test_user.id, name="python", source="manual", proficiency="intermediate"),
        Skill(user_id=test_user.id, name="django", source="manual", proficiency="intermediate"),
        Skill(user_id=test_user.id, name="postgresql", source="manual", proficiency="beginner"),
    ]
    
    for skill in skills:
        db.add(skill)
    db.commit()
    
    return test_user