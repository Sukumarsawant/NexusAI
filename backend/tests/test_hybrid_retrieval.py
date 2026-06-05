import pytest
from app.models.document import Document, DocumentChunk
from app.retrieval.hybrid_search import reciprocal_rank_fusion
from app.retrieval.engine import RetrievalEngine


def test_reciprocal_rank_fusion():
    v_results = [
        {"chunk_id": "c1", "similarity_score": 0.95, "content": "text 1"},
        {"chunk_id": "c2", "similarity_score": 0.85, "content": "text 2"},
    ]
    k_results = [
        {"chunk_id": "c2", "similarity_score": 0.90, "content": "text 2"},
        {"chunk_id": "c3", "similarity_score": 0.70, "content": "text 3"},
    ]

    fused = reciprocal_rank_fusion(v_results, k_results, k=60, alpha=0.5)
    assert len(fused) == 3
    # c2 appears in both vector and keyword, so it should rank highest!
    assert fused[0]["chunk_id"] == "c2"
    assert fused[0]["similarity_score"] > fused[1]["similarity_score"]


def test_retrieval_engine_search(db_session, test_user):
    # Insert test document & chunks
    doc = Document(
        id="doc-test-1",
        user_id=test_user.id,
        filename="TestPolicy.txt",
        file_type="txt",
        file_size=500,
        content_hash="testhash123",
        status="indexed",
        chunk_count=2,
    )
    db_session.add(doc)

    c1 = DocumentChunk(
        id="chunk-test-1",
        document_id=doc.id,
        user_id=test_user.id,
        chunk_index=0,
        content="The retention policy mandates that records are archived for 7 years.",
        chunk_metadata={"page_number": 1},
    )
    c2 = DocumentChunk(
        id="chunk-test-2",
        document_id=doc.id,
        user_id=test_user.id,
        chunk_index=1,
        content="Employee access control is enforced through multi-factor authentication.",
        chunk_metadata={"page_number": 2},
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    res = RetrievalEngine.search(
        db=db_session,
        query="retention policy 7 years",
        user_id=test_user.id,
        strategy="keyword",
        top_k=2,
        apply_rerank=False,
    )

    assert res["total_results"] >= 1
    assert "retention policy" in res["constructed_context"].lower()
    assert res["results"][0]["filename"] == "TestPolicy.txt"
