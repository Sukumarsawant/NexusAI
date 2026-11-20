import os
import sys
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set SQLite test database in environment
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.config import settings
settings.DATABASE_URL = "sqlite:///:memory:"

import app.core.database as db_module
from app.core.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.services.gemini_client import gemini_service

# Rebind test engine to SQLite using StaticPool so in-memory DB is shared across threads/connections
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Monkeypatch database module engine and SessionLocal
db_module.engine = test_engine
db_module.SessionLocal = TestingSessionLocal

# Create all tables on the shared in-memory database
Base.metadata.create_all(bind=test_engine)

from app.main import app


@pytest.fixture(autouse=True)
def mock_gemini_for_unit_tests(monkeypatch):
    """
    Mock Gemini LLM and Embedding calls in unit tests to ensure fast,
    deterministic test runs without requiring network access.
    """
    def fake_generate_text(prompt, system_instruction=None, model=None, temperature=0.0, json_output=False):
        if json_output:
            if "sufficient" in prompt.lower():
                return '{"sufficient": true, "reason": "Sufficient context found."}', 20, 10
            if "intent" in prompt.lower():
                import re
                if re.search(r"\b(hello|hi|hey|good morning|good evening)\b", prompt.lower()):
                    return '{"intent": "general_conversation", "question_type": "conversational", "entities": [], "needs_retrieval": false, "rewritten_query": ""}', 20, 15
                return '{"intent": "factual_inquiry", "question_type": "analytical", "entities": ["compliance"], "needs_retrieval": true, "rewritten_query": "search query"}', 30, 25
            if "reasoning_draft" in prompt.lower():
                return '{"reasoning_draft": "Verified draft answer grounded in evidence.", "contradictions": []}', 40, 20
            if "passed" in prompt.lower():
                return '{"passed": true, "unsupported_claims": [], "critique": ""}', 35, 15
            if "score" in prompt.lower() or "scale of 0 to 10" in prompt.lower():
                return '[{"index": 0, "score": 9.0}]', 50, 10
            return '{"status": "ok"}', 10, 5
        return "Based on the verified enterprise records, policies are enforced.", 30, 15

    def fake_generate_embeddings(texts, model=None):
        return [[0.05] * settings.EMBEDDING_DIMENSION for _ in texts]

    monkeypatch.setattr(gemini_service, "generate_text", fake_generate_text)
    monkeypatch.setattr(gemini_service, "generate_embeddings", fake_generate_embeddings)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def test_user(db_session):
    existing = db_session.query(User).filter(User.email == "analyst@enterprise.com").first()
    if existing:
        return existing
    user = User(
        email="analyst@enterprise.com",
        hashed_password=hash_password("Secr3tPassword!"),
        full_name="Enterprise Analyst",
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
