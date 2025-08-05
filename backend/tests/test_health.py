# backend/tests/test_health.py

import pytest
from fastapi.testclient import TestClient

def test_health_endpoint(client: TestClient):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_root_endpoint(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

def test_nonexistent_endpoint(client: TestClient):
    """Test that nonexistent endpoints return 404."""
    response = client.get("/this-endpoint-does-not-exist")
    assert response.status_code == 404

def test_database_connection(db):
    """Test that we can connect to the test database."""
    from sqlalchemy import text
    
    # Execute a simple query
    result = db.execute(text("SELECT 1"))
    assert result.scalar() == 1

def test_create_user_in_test_db(db):
    """Test creating a user in the test database."""
    from app.db.models import User
    from app.core.security import get_password_hash
    
    # Create a user
    user = User(
        email="newuser@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="New User"
    )
    db.add(user)
    db.commit()
    
    # Query the user
    saved_user = db.query(User).filter(User.email == "newuser@example.com").first()
    assert saved_user is not None
    assert saved_user.full_name == "New User"

def test_redis_connection():
    """Test that we can connect to Redis."""
    from app.core.cache import redis_client
    
    if redis_client:
        # Test ping
        assert redis_client.ping() == True
        
        # Test set/get
        redis_client.set("test_key", "test_value", ex=10)
        assert redis_client.get("test_key").decode() == "test_value"
        
        # Cleanup
        redis_client.delete("test_key")