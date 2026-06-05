import io
import pytest
from app.models.document import Document


def test_document_upload_and_duplicate_rejection(client, auth_headers):
    file_bytes = b"Corporate security guideline 2026. Data must be encrypted using AES-256."
    files = {"file": ("guideline.txt", io.BytesIO(file_bytes), "text/plain")}

    # First upload
    res = client.post("/api/documents/upload", files=files, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["filename"] == "guideline.txt"
    assert data["status"] in ("indexed", "processing")
    doc_id = data["id"]

    # Duplicate upload rejection
    files2 = {"file": ("guideline_copy.txt", io.BytesIO(file_bytes), "text/plain")}
    dup_res = client.post("/api/documents/upload", files=files2, headers=auth_headers)
    assert dup_res.status_code == 409
    assert "duplicate" in dup_res.json()["detail"].lower()


def test_user_document_isolation(client, db_session, test_user):
    from app.core.security import hash_password, create_access_token
    from app.models.user import User

    # Create User B
    user_b = User(
        email="user_b@enterprise.com",
        hashed_password=hash_password("UserBPassword!"),
        full_name="User B",
    )
    db_session.add(user_b)
    db_session.commit()
    token_b = create_access_token(user_b.id)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Upload document as User A
    token_a = create_access_token(test_user.id)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    files = {"file": ("secret_a.txt", io.BytesIO(b"Confidential payload for User A only."), "text/plain")}
    res_a = client.post("/api/documents/upload", files=files, headers=headers_a)
    assert res_a.status_code == 200
    doc_id_a = res_a.json()["id"]

    # User B lists documents - should NOT see User A's document
    list_b = client.get("/api/documents", headers=headers_b)
    assert list_b.status_code == 200
    assert not any(d["id"] == doc_id_a for d in list_b.json())

    # User B attempts to delete User A's document - should 404
    del_res = client.delete(f"/api/documents/{doc_id_a}", headers=headers_b)
    assert del_res.status_code == 404


def test_health_and_readiness_endpoints(client):
    h = client.get("/health")
    assert h.status_code == 200
    assert h.json()["status"] == "healthy"

    r = client.get("/ready")
    assert r.status_code == 200
    assert "database" in r.json()
