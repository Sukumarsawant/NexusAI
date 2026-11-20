import pytest
from fastapi.testclient import TestClient
from app.models.document import Document, DocumentChunk
from app.models.conversation import Conversation
from app.models.observability import AgentTrace


def test_cross_tenant_document_access_blocked(client: TestClient, auth_headers: dict, test_user):
    # Register and login a second tenant (User B)
    res_b = client.post("/api/auth/register", json={
        "email": "user_b@tenant.com",
        "password": "Password123!",
        "full_name": "Tenant B User"
    })
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A uploads a document
    res_upload = client.post(
        "/api/documents/upload",
        files={"file": ("tenant_a_confidential.txt", b"Secret data owned by Tenant A", "text/plain")},
        headers=auth_headers,
    )
    assert res_upload.status_code == 200
    doc_a_id = res_upload.json()["id"]

    # User B attempts to access User A's document -> 404 NOT FOUND
    res_get = client.get(f"/api/documents/{doc_a_id}", headers=headers_b)
    assert res_get.status_code == 404
    assert res_get.json()["detail"] == "Document not found"

    # User B attempts to delete User A's document -> 404 NOT FOUND
    res_del = client.delete(f"/api/documents/{doc_a_id}", headers=headers_b)
    assert res_del.status_code == 404

    # User B lists documents -> User A's document is NOT in the list
    res_list = client.get("/api/documents", headers=headers_b)
    assert res_list.status_code == 200
    doc_ids_b = [d["id"] for d in res_list.json()]
    assert doc_a_id not in doc_ids_b


def test_cross_tenant_search_isolation(client: TestClient, auth_headers: dict, db_session, test_user):
    # Register Tenant B
    res_b = client.post("/api/auth/register", json={
        "email": "user_search_b@tenant.com",
        "password": "Password123!",
        "full_name": "Tenant B Search"
    })
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A uploads document with distinct keyword
    client.post(
        "/api/documents/upload",
        files={"file": ("falcon_project.txt", b"Project Falcon secret blueprints for Tenant A.", "text/plain")},
        headers=auth_headers,
    )

    # User B searches for 'Falcon'
    search_res = client.post(
        "/api/retrieval/search",
        json={"query": "Falcon blueprints", "strategy": "keyword", "top_k": 5},
        headers=headers_b,
    )
    assert search_res.status_code == 200
    results = search_res.json()["results"]
    # User B must get 0 results for User A's confidential document
    assert len(results) == 0


def test_cross_tenant_conversation_isolation(client: TestClient, auth_headers: dict):
    # Register Tenant B
    res_b = client.post("/api/auth/register", json={
        "email": "user_conv_b@tenant.com",
        "password": "Password123!",
        "full_name": "Tenant B Conv"
    })
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A chats
    chat_a = client.post(
        "/api/chat",
        json={"query": "Hello from Tenant A", "top_k": 3},
        headers=auth_headers,
    )
    assert chat_a.status_code == 200
    conv_id = chat_a.json()["conversation_id"]

    # User B attempts to access User A's conversation -> 404
    get_conv = client.get(f"/api/conversations/{conv_id}", headers=headers_b)
    assert get_conv.status_code == 404

    # User B attempts to delete User A's conversation -> 404
    del_conv = client.delete(f"/api/conversations/{conv_id}", headers=headers_b)
    assert del_conv.status_code == 404
