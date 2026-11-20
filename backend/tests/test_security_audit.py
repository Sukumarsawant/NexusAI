import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.ingestion.pipeline import IngestionPipeline


def test_path_traversal_upload_sanitized(client: TestClient, auth_headers: dict):
    # Attempting directory traversal via malicious filename
    malicious_filename = "../../../../etc/passwd.txt"
    res = client.post(
        "/api/documents/upload",
        files={"file": (malicious_filename, b"root:x:0:0:root:/root:/bin/bash", "text/plain")},
        headers=auth_headers,
    )
    assert res.status_code == 200
    uploaded_name = res.json()["filename"]
    # Filename must be stripped of traversal path characters
    assert ".." not in uploaded_name
    assert "/" not in uploaded_name
    assert "\\" not in uploaded_name
    assert uploaded_name == "passwd.txt"


def test_unsupported_file_extension_rejected(client: TestClient, auth_headers: dict):
    res = client.post(
        "/api/documents/upload",
        files={"file": ("malicious_script.exe", b"binary content", "application/octet-stream")},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]


def test_empty_file_upload_rejected(client: TestClient, auth_headers: dict):
    res = client.post(
        "/api/documents/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_unauthenticated_requests_strictly_blocked(client: TestClient):
    # Documents endpoint
    res1 = client.get("/api/documents")
    assert res1.status_code == 401

    # Chat endpoint
    res2 = client.post("/api/chat", json={"query": "test"})
    assert res2.status_code == 401

    # Retrieval endpoint
    res3 = client.post("/api/retrieval/search", json={"query": "test"})
    assert res3.status_code == 401

    # Observability endpoint
    res4 = client.get("/api/observability/overview")
    assert res4.status_code == 401


def test_invalid_jwt_token_rejected(client: TestClient):
    fake_headers = {"Authorization": "Bearer invalid.jwt.token.here"}
    res = client.get("/api/documents", headers=fake_headers)
    assert res.status_code == 401


def test_production_zero_embeddings_guard(db_session):
    import os
    # When in production and not testing, unconfigured API key must raise RuntimeError
    old_env = settings.ENVIRONMENT
    settings.ENVIRONMENT = "production"
    
    # Temporarily remove TESTING flag to test production protection
    testing_flag = os.environ.pop("TESTING", None)
    try:
        from app.models.document import Document
        dummy_doc = Document(
            id="test-prod-guard",
            user_id="user-1",
            filename="test.txt",
            file_type="txt",
            file_size=10,
            content_hash="h1",
            storage_path="nonexistent.txt",
            status="pending"
        )
        db_session.add(dummy_doc)
        db_session.commit()

        with pytest.raises(Exception):
            IngestionPipeline.process_document(db_session, "test-prod-guard")
    finally:
        settings.ENVIRONMENT = old_env
        if testing_flag:
            os.environ["TESTING"] = testing_flag
