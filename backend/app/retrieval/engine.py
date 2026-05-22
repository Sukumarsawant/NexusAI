import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.retrieval.vector_search import vector_search
from app.retrieval.keyword_search import keyword_search
from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.reranker import Reranker


class RetrievalEngine:
    @staticmethod
    def search(
        db: Session,
        query: str,
        user_id: str,
        strategy: str = "hybrid",
        top_k: int = settings.DEFAULT_TOP_K,
        alpha: float = settings.HYBRID_ALPHA,
        filter_doc_ids: Optional[List[str]] = None,
        apply_rerank: bool = True,
    ) -> Dict[str, Any]:
        """
        Coordinated retrieval returning structured results with citations, scores, and context.
        """
        start_time = time.time()
        strat = strategy.lower()

        if strat == "vector":
            candidates = vector_search(
                db=db,
                query_text=query,
                user_id=user_id,
                top_k=top_k * 2 if apply_rerank else top_k,
                filter_doc_ids=filter_doc_ids,
            )
        elif strat == "keyword":
            candidates = keyword_search(
                db=db,
                query_text=query,
                user_id=user_id,
                top_k=top_k * 2 if apply_rerank else top_k,
                filter_doc_ids=filter_doc_ids,
            )
        else:  # hybrid
            candidates = hybrid_search(
                db=db,
                query_text=query,
                user_id=user_id,
                top_k=top_k * 2 if apply_rerank else top_k,
                alpha=alpha,
                filter_doc_ids=filter_doc_ids,
            )

        # Apply reranker
        if apply_rerank and candidates:
            final_results = Reranker.rerank(query=query, candidates=candidates, top_k=top_k)
        else:
            final_results = candidates[:top_k]

        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Context construction
        context_blocks = []
        for i, item in enumerate(final_results, start=1):
            meta = item.get("metadata", {})
            page_or_row = None
            if "page_number" in meta:
                page_or_row = f"Page {meta['page_number']}"
            elif "row_start" in meta:
                page_or_row = f"Rows {meta['row_start']}-{meta.get('row_end', meta['row_start'])}"

            item["page_or_row"] = page_or_row
            block = f"[Source {i}: {item['filename']} {f'({page_or_row})' if page_or_row else ''} - Score: {item['similarity_score']}]\n{item['content']}"
            context_blocks.append(block)

        constructed_context = "\n\n".join(context_blocks)

        return {
            "query": query,
            "strategy": strategy,
            "total_results": len(final_results),
            "results": final_results,
            "constructed_context": constructed_context,
            "duration_ms": duration_ms,
        }
