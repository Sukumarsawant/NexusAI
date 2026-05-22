import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.document import DocumentChunk, Document
from app.core.config import settings


def keyword_search(
    db: Session,
    query_text: str,
    user_id: str,
    top_k: int = 5,
    filter_doc_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    clean_query = query_text.strip()
    if not clean_query:
        return []

    is_postgres = "postgresql" in settings.DATABASE_URL.lower()

    if is_postgres:
        doc_filter_clause = ""
        params: Dict[str, Any] = {
            "user_id": user_id,
            "q": clean_query,
            "top_k": top_k * 2,
        }
        if filter_doc_ids:
            doc_filter_clause = "AND c.document_id = ANY(:doc_ids)"
            params["doc_ids"] = filter_doc_ids

        sql = text(f"""
            SELECT 
                c.id, c.document_id, c.chunk_index, c.content, c.metadata,
                d.filename,
                ts_rank_cd(to_tsvector('english', c.content), websearch_to_tsquery('english', :q)) AS rank
            FROM document_chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.user_id = :user_id 
              AND to_tsvector('english', c.content) @@ websearch_to_tsquery('english', :q)
              {doc_filter_clause}
            ORDER BY rank DESC
            LIMIT :top_k;
        """)

        try:
            results = db.execute(sql, params).fetchall()
            if results:
                max_rank = max((float(r[6] or 0.0) for r in results), default=1.0) or 1.0
                return [
                    {
                        "chunk_id": str(r[0]),
                        "document_id": str(r[1]),
                        "chunk_index": int(r[2]),
                        "content": str(r[3]),
                        "metadata": dict(r[4] or {}),
                        "filename": str(r[5]),
                        "similarity_score": min(1.0, float(r[6] or 0.0) / max_rank),
                        "retrieval_method": "keyword",
                    }
                    for r in results
                ]
        except Exception:
            pass

    tokens = [re.escape(t.lower()) for t in re.findall(r"\w+", clean_query) if len(t) > 2]
    if not tokens:
        tokens = [clean_query.lower()]

    query = (
        db.query(DocumentChunk, Document.filename)
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(DocumentChunk.user_id == user_id)
    )
    if filter_doc_ids:
        query = query.filter(DocumentChunk.document_id.in_(filter_doc_ids))

    chunks = query.all()
    results = []

    for chunk, filename in chunks:
        content_lower = chunk.content.lower()
        match_count = sum(content_lower.count(token) for token in tokens)
        if match_count > 0:
            score = min(1.0, match_count / (len(tokens) * 3))
            results.append({
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "metadata": chunk.chunk_metadata or {},
                "filename": filename,
                "similarity_score": score,
                "retrieval_method": "keyword",
            })

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:top_k * 2]
