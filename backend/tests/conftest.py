"""
Pytest fixtures and configuration
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.config import settings


# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="function")
def test_db():
    """
    Create a test database for each test function.
    """
    # Create test database engine
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}  # Needed for SQLite
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """
    Create a test client with test database.
    """
    # Override get_db dependency
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_prompt_content():
    """Sample prompt content for testing"""
    return """Ты - тестовый помощник-хостес ресторана {restaurant_name}.

Отвечай кратко и по делу.

Дата: {date}
Время: {time}
"""


@pytest.fixture
def sample_user_message():
    """Sample user message for testing"""
    return "Здравствуйте, хочу забронировать столик"


@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing"""
    return {
        "message": "Здравствуйте, хочу забронировать столик",
        "conversation_id": None,
        "generate_audio": False
    }
