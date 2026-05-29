import time
import logging
from typing import Dict, Any, List
from app.agents.state import NexusAgentState
from app.services.gemini_client import gemini_service

logger = logging.getLogger("nexusai.agents.response")


def response_agent(state: NexusAgentState) -> Dict[str, Any]:
    """
    Response Agent:
    - Formats the verified answer with clear typography and structure
    - Generates definitive citations linked to source files and page/row indices
    - Clearly distinguishes verified facts from uncertainty
    """
    start_time = time.time()
    traces = list(state.get("agent_traces", []))
    total_in = state.get("total_input_tokens", 0)
    total_out = state.get("total_output_tokens", 0)

    draft = state.get("reasoning_draft", "")
    context = state.get("context_text", "")
    chunks = state.get("retrieved_chunks", [])
    unsupported = state.get("unsupported_claims", [])
    contradictions = state.get("identified_contradictions", [])
    query = state.get("query", "")

    final_answer = ""
    citations: List[Dict[str, Any]] = []
    confidence = "high"
    is_grounded = True
    input_tokens = 0
    output_tokens = 0

    # Build citations from retrieved chunks
    for i, c in enumerate(chunks, start=1):
        meta = c.get("metadata", {})
        page_or_row = c.get("page_or_row")
        snippet = c.get("content", "")[:180] + "..."
        citations.append({
            "source_id": str(i),
            "filename": c.get("filename", "Unknown"),
            "chunk_index": c.get("chunk_index", 0),
            "page_or_row": page_or_row,
            "snippet": snippet,
            "relevance_score": c.get("similarity_score", 0.0),
        })

    if not chunks or "cannot find sufficient information" in draft.lower():
        confidence = "low"
        is_grounded = False
        final_answer = (
            "I could not locate sufficient verified information within your uploaded documents "
            "to answer your question with certainty. Please upload relevant source documentation or refine your query."
        )
    elif gemini_service.is_configured():
        prompt = (
            f"User Question: \"{query}\"\n\n"
            f"Verified Draft Answer:\n{draft}\n\n"
            f"Unsupported Claims to exclude:\n{unsupported}\n\n"
            f"Contradictions noted:\n{contradictions}\n\n"
            "Format the final response for an enterprise audience:\n"
            "- Use clear, professional markdown with headings or bullet points.\n"
            "- Include exact source attributions (e.g. `[Source 1: filename, Page X]`).\n"
            "- Explicitly state any limitations or ambiguities.\n"
            "- Do not make up facts."
        )
        try:
            resp_text, in_tok, out_tok = gemini_service.generate_text(
                prompt=prompt,
                system_instruction="You are an enterprise knowledge intelligence assistant delivering transparent, well-cited answers.",
                temperature=0.2,
            )
            input_tokens = in_tok
            output_tokens = out_tok
            final_answer = resp_text.strip()
            confidence = "high" if len(chunks) >= 2 and not unsupported else "medium"
        except Exception as e:
            logger.warning(f"Response Agent fallback: {e}")
            final_answer = draft
    else:
        final_answer = draft

    duration_ms = round((time.time() - start_time) * 1000, 2)
    traces.append({
        "agent_name": "Response Agent",
        "execution_order": len(traces) + 1,
        "duration_ms": duration_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "status": "success",
        "summary": f"Generated final answer with {len(citations)} citations. Confidence: {confidence}",
    })

    return {
        "final_answer": final_answer,
        "citations": citations,
        "confidence": confidence,
        "is_grounded": is_grounded,
        "agent_traces": traces,
        "total_input_tokens": total_in + input_tokens,
        "total_output_tokens": total_out + output_tokens,
    }
