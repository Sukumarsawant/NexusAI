import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.document import DocumentChunk, Document
from app.services.gemini_client import gemini_service
from app.core.config import settings


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def vector_search(
    db: Session,
    query_text: str,
    user_id: str,
    top_k: int = 5,
    filter_doc_ids: Optional[List[str]] = None,
    query_vector: Optional[List[float]] = None,
) -> List[Dict[str, Any]]:
    if query_vector is None:
        if gemini_service.is_configured():
            embeddings = gemini_service.generate_embeddings([query_text])
            query_vector = embeddings[0] if embeddings else [0.0] * settings.EMBEDDING_DIMENSION
        else:
            query_vector = [0.0] * settings.EMBEDDING_DIMENSION

    is_postgres = "postgresql" in settings.DATABASE_URL.lower()

    if is_postgres:
        doc_filter_clause = ""
        params: Dict[str, Any] = {
            "user_id": user_id,
            "qvec": str(query_vector),
            "top_k": top_k * 2,
        }
        if filter_doc_ids:
            doc_filter_clause = "AND c.document_id = ANY(:doc_ids)"
            params["doc_ids"] = filter_doc_ids

        sql = text(f"""
            SELECT 
                c.id, c.document_id, c.chunk_index, c.content, c.metadata,
                d.filename,
                1 - (c.embedding <=> :qvec::vector) AS similarity_score
            FROM document_chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.user_id = :user_id {doc_filter_clause}
            ORDER BY c.embedding <=> :qvec::vector ASC
            LIMIT :top_k;
        """)

        try:
            results = db.execute(sql, params).fetchall()
            return [
                {
                    "chunk_id": str(r[0]),
                    "document_id": str(r[1]),
                    "chunk_index": int(r[2]),
                    "content": str(r[3]),
                    "metadata": dict(r[4] or {}),
                    "filename": str(r[5]),
                    "similarity_score": float(r[6] or 0.0),
                    "retrieval_method": "vector",
                }
                for r in results
            ]
        except Exception:
            pass

    query = (
        db.query(DocumentChunk, Document.filename)
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(DocumentChunk.user_id == user_id)
    )
    if filter_doc_ids:
        query = query.filter(DocumentChunk.document_id.in_(filter_doc_ids))

    chunks = query.all()
    scored_chunks = []
    for chunk, filename in chunks:
        vec = chunk.embedding
        score = 0.0
        if vec and query_vector:
            score = cosine_similarity(query_vector, vec)
        scored_chunks.append({
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "metadata": chunk.chunk_metadata or {},
            "filename": filename,
            "similarity_score": score,
            "retrieval_method": "vector",
        })

    scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored_chunks[:top_k * 2]
