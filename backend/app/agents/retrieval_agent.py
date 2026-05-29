import time
import json
import logging
from typing import Dict, Any, List
from app.agents.state import NexusAgentState
from app.core.database import SessionLocal
from app.models.document import Document
from app.retrieval.engine import RetrievalEngine
from app.services.gemini_client import gemini_service

logger = logging.getLogger("nexusai.agents.retrieval")


def retrieval_agent(state: NexusAgentState) -> Dict[str, Any]:
    """
    Retrieval Agent:
    - Calls hybrid retrieval engine
    - Evaluates whether retrieved context is sufficient to answer the query
    - Flags if additional search iterations are required
    """
    start_time = time.time()
    traces = list(state.get("agent_traces", []))
    total_in = state.get("total_input_tokens", 0)
    total_out = state.get("total_output_tokens", 0)
    user_id = state.get("user_id", "")
    top_k = state.get("top_k", 5)
    cycle = state.get("retrieval_cycle", 0) + 1

    # Choose query to search: rewritten or original or augmented
    search_query = state.get("rewritten_query") or state.get("query", "")
    if state.get("verification_feedback"):
        # Augment search with verification critique if looping back
        search_query = f"{search_query} {state.get('verification_feedback')}"

    # Resolve document filter if filenames specified
    filter_doc_ids = None
    filenames = state.get("filter_filenames")
    db = SessionLocal()
    try:
        if filenames:
            docs = db.query(Document.id).filter(
                Document.user_id == user_id,
                Document.filename.in_(filenames)
            ).all()
            filter_doc_ids = [d[0] for d in docs]

        search_res = RetrievalEngine.search(
            db=db,
            query=search_query,
            user_id=user_id,
            strategy="hybrid",
            top_k=top_k,
            filter_doc_ids=filter_doc_ids,
            apply_rerank=True,
        )
    finally:
        db.close()

    chunks = search_res.get("results", [])
    context_text = search_res.get("constructed_context", "")

    # Sufficiency Check
    context_sufficient = True
    input_tokens = 0
    output_tokens = 0

    if not chunks:
        context_sufficient = False
    elif gemini_service.is_configured():
        prompt = (
            f"User Query: \"{state.get('query')}\"\n\n"
            f"Retrieved Context:\n{context_text[:2000]}\n\n"
            "Determine if this retrieved context contains sufficient evidence to answer the query.\n"
            "Respond in JSON format: {\"sufficient\": true or false, \"reason\": \"short explanation\"}"
        )
        try:
            resp_text, in_tok, out_tok = gemini_service.generate_text(
                prompt=prompt,
                system_instruction="You are an enterprise retrieval auditor.",
                temperature=0.0,
                json_output=True,
            )
            input_tokens = in_tok
            output_tokens = out_tok
            data = json.loads(resp_text)
            context_sufficient = data.get("sufficient", True)
        except Exception as e:
            logger.warning(f"Sufficiency check fallback: {e}")
            context_sufficient = len(chunks) > 0

    duration_ms = round((time.time() - start_time) * 1000, 2)
    traces.append({
        "agent_name": "Retrieval Agent",
        "execution_order": len(traces) + 1,
        "duration_ms": duration_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "status": "success",
        "summary": f"Retrieved {len(chunks)} chunks (Cycle {cycle}). Sufficient: {context_sufficient}",
    })

    return {
        "retrieved_chunks": chunks,
        "context_text": context_text,
        "context_sufficient": context_sufficient,
        "retrieval_cycle": cycle,
        "agent_traces": traces,
        "total_input_tokens": total_in + input_tokens,
        "total_output_tokens": total_out + output_tokens,
    }
