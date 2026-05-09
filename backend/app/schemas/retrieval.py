from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    strategy: str = "hybrid"  # "hybrid" | "vector" | "keyword"
    alpha: float = 0.5  # Weight between vector (1.0) and keyword (0.0)
    filter_metadata: Optional[Dict[str, Any]] = None


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    chunk_index: int
    content: str
    similarity_score: float
    page_or_row: Optional[str] = None
    metadata: Dict[str, Any]
    retrieval_method: str  # vector, keyword, hybrid_rrf


class SearchResponse(BaseModel):
    query: str
    total_results: int
    strategy: str
    results: List[SearchResultItem]
    search_duration_ms: float
