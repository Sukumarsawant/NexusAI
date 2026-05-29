import time
import json
import logging
from typing import Dict, Any
from app.agents.state import NexusAgentState
from app.services.gemini_client import gemini_service

logger = logging.getLogger("nexusai.agents.reasoning")


def reasoning_agent(state: NexusAgentState) -> Dict[str, Any]:
    """
    Reasoning Agent:
    - Analyzes and synthesizes information across retrieved documents
    - Identifies relationships and potential contradictions
    - Drafts an answer grounded strictly on retrieved evidence
    """
    start_time = time.time()
    traces = list(state.get("agent_traces", []))
    total_in = state.get("total_input_tokens", 0)
    total_out = state.get("total_output_tokens", 0)

    query = state.get("query", "")
    context = state.get("context_text", "")
    contradictions = []
    draft = ""
    input_tokens = 0
    output_tokens = 0

    if not context or not state.get("retrieved_chunks"):
        draft = "I cannot find sufficient information in the provided knowledge base to answer this question accurately."
    elif gemini_service.is_configured():
        prompt = (
            f"User Question: \"{query}\"\n\n"
            f"Retrieved Evidence:\n{context}\n\n"
            "Task:\n"
            "1. Synthesize an evidence-based answer addressing the question.\n"
            "2. Note any contradictions or data discrepancies between sources.\n"
            "3. Ground all statements in the retrieved excerpts.\n\n"
            "Respond in JSON format:\n"
            "{\n"
            "  \"reasoning_draft\": \"Draft answer text with inline [Source X] references.\",\n"
            "  \"contradictions\": [\"List any conflicting statements across sources\"]\n"
            "}"
        )
        try:
            resp_text, in_tok, out_tok = gemini_service.generate_text(
                prompt=prompt,
                system_instruction="You are a rigorous Enterprise Reasoning Agent. You analyze evidence and avoid speculation.",
                temperature=0.2,
                json_output=True,
            )
            input_tokens = in_tok
            output_tokens = out_tok
            data = json.loads(resp_text)
            draft = data.get("reasoning_draft", "")
            contradictions = data.get("contradictions", [])
        except Exception as e:
            logger.warning(f"Reasoning Agent LLM fallback: {e}")
            draft = f"Based on retrieved documentation: {context[:500]}"
    else:
        draft = f"Retrieved context summary:\n{context[:400]}"

    duration_ms = round((time.time() - start_time) * 1000, 2)
    traces.append({
        "agent_name": "Reasoning Agent",
        "execution_order": len(traces) + 1,
        "duration_ms": duration_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "status": "success",
        "summary": f"Drafted synthesis ({len(draft)} chars). Contradictions found: {len(contradictions)}",
    })

    return {
        "reasoning_draft": draft,
        "identified_contradictions": contradictions,
        "agent_traces": traces,
        "total_input_tokens": total_in + input_tokens,
        "total_output_tokens": total_out + output_tokens,
    }
