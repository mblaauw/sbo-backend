# tests/test_skills_service.py
"""
Unit tests for the Skills Service.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.database import Base, get_db
from services.skills_service import app
import os
import json

# Set up a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_skills.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Test client
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_and_teardown_db():
    # Set up
    Base.metadata.create_all(bind=engine)
    yield
    # Tear down
    Base.metadata.drop_all(bind=engine)

def test_health(setup_and_teardown_db):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_skill_categories(setup_and_teardown_db):
    """Test getting skill categories"""
    response = client.get("/skills/categories")
    assert response.status_code == 200
    # The startup event should have created mock categories
    assert len(response.json()) > 0
    categories = response.json()
    assert "id" in categories[0]
    assert "name" in categories[0]
    assert "description" in categories[0]

def test_get_skills_by_category(setup_and_teardown_db):
    """Test getting skills by category"""
    # First get all categories
    categories_response = client.get("/skills/categories")
    assert categories_response.status_code == 200
    categories = categories_response.json()
    
    # Then get skills for the first category
    if categories:
        category_id = categories[0]["id"]
        skills_response = client.get(f"/skills/category/{category_id}")
        assert skills_response.status_code == 200
        skills = skills_response.json()
        
        # Check that skills have the expected structure
        if skills:
            assert "id" in skills[0]
            assert "name" in skills[0]
            assert "description" in skills[0]
            assert "category_id" in skills[0]
            assert skills[0]["category_id"] == category_id

def test_extract_skills_from_text(setup_and_teardown_db, monkeypatch):
    """Test extracting skills from text"""
    # Mock the LLM service call
    async def mock_post(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
            
            def json(self):
                return self.json_data
            
            @property
            def status_code(self):
                return self.status_code
                
        return MockResponse([
            {
                "skill_name": "Python",
                "confidence": 0.95,
                "context": "I've been using Python for 5 years"
            },
            {
                "skill_name": "SQL",
                "confidence": 0.85,
                "context": "SQL database querying"
            }
        ], 200)
    
    # Apply the mock
    import httpx
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    
    # Test the endpoint
    response = client.post(
        "/skills/extract",
        json={"text": "I've been using Python for 5 years and have experience with SQL database querying."}
    )
    
    assert response.status_code == 200
    skills = response.json()
    assert len(skills) > 0
    assert "skill_name" in skills[0]
    assert "confidence" in skills[0]