from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.retrieval.vector_search import vector_search
from app.retrieval.keyword_search import keyword_search
from app.core.config import settings


def reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]],
    keyword_results: List[Dict[str, Any]],
    k: int = 60,
    alpha: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Combines vector search and keyword search results using Reciprocal Rank Fusion (RRF).
    score(d) = alpha * (1 / (k + rank_v(d))) + (1 - alpha) * (1 / (k + rank_k(d)))
    """
    scores: Dict[str, float] = {}
    items: Dict[str, Dict[str, Any]] = {}

    for rank, item in enumerate(vector_results, start=1):
        cid = item["chunk_id"]
        items[cid] = item
        scores[cid] = scores.get(cid, 0.0) + (alpha * (1.0 / (k + rank)))

    for rank, item in enumerate(keyword_results, start=1):
        cid = item["chunk_id"]
        if cid not in items:
            items[cid] = item
        scores[cid] = scores.get(cid, 0.0) + ((1.0 - alpha) * (1.0 / (k + rank)))

    # Normalize fusion scores to 0.0 - 1.0 range
    max_score = max(scores.values()) if scores else 1.0
    fused_results = []
    for cid, rrf_score in scores.items():
        entry = dict(items[cid])
        entry["similarity_score"] = round(rrf_score / max_score if max_score > 0 else 0.0, 4)
        entry["retrieval_method"] = "hybrid_rrf"
        fused_results.append(entry)

    fused_results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return fused_results


def hybrid_search(
    db: Session,
    query_text: str,
    user_id: str,
    top_k: int = 5,
    alpha: float = settings.HYBRID_ALPHA,
    filter_doc_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Execute both vector and keyword queries in parallel, then apply RRF fusion.
    """
    v_results = vector_search(
        db=db,
        query_text=query_text,
        user_id=user_id,
        top_k=top_k,
        filter_doc_ids=filter_doc_ids,
    )
    k_results = keyword_search(
        db=db,
        query_text=query_text,
        user_id=user_id,
        top_k=top_k,
        filter_doc_ids=filter_doc_ids,
    )

    fused = reciprocal_rank_fusion(v_results, k_results, k=60, alpha=alpha)
    return fused[:top_k]
