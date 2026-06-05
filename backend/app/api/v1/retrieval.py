from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.retrieval import SearchRequest, SearchResponse, SearchResultItem
from app.retrieval.engine import RetrievalEngine

router = APIRouter(prefix="/retrieval", tags=["Retrieval Engine"])


@router.post("/search", response_model=SearchResponse)
def execute_search(
    req: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    search_res = RetrievalEngine.search(
        db=db,
        query=req.query,
        user_id=current_user.id,
        strategy=req.strategy,
        top_k=req.top_k,
        alpha=req.alpha,
        apply_rerank=True,
    )

    items = [
        SearchResultItem(
            chunk_id=r["chunk_id"],
            document_id=r["document_id"],
            filename=r["filename"],
            chunk_index=r["chunk_index"],
            content=r["content"],
            similarity_score=r["similarity_score"],
            page_or_row=r.get("page_or_row"),
            metadata=r.get("metadata", {}),
            retrieval_method=r.get("retrieval_method", "hybrid_rrf"),
        )
        for r in search_res.get("results", [])
    ]

    return SearchResponse(
        query=req.query,
        total_results=len(items),
        strategy=req.strategy,
        results=items,
        search_duration_ms=search_res.get("duration_ms", 0.0),
    )
